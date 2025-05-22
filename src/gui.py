# src/gui.py
import sys  # For system-specific parameters and functions, like sys.exit and sys.argv
import os   # For operating system dependent functionality, like path manipulation
import time # For time-related functions, used here for progress bar simulation
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                            QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QTextEdit, QFileDialog, QProgressBar, QRadioButton,
                            QGroupBox, QLineEdit, QMessageBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal # Core Qt functionalities, threading, and signals
from PyQt6.QtGui import QFont, QIcon, QPixmap # For styling, icons, and images

# Import core steganography functions from the 'core' module
# Assumes 'core.py' is in the same directory or accessible via sys.path
from core import embed_message, extract_message

class WorkerThread(QThread):
    """
    Worker thread for long-running tasks like embedding or extracting messages.
    This prevents the UI from freezing during these operations.
    """
    progress = pyqtSignal(int)      # Signal to update progress bar
    message = pyqtSignal(str)       # Signal to send status messages to the UI
    result = pyqtSignal(dict)       # Signal to send the result of the task (e.g., output file, extracted message)
    error = pyqtSignal(str)         # Signal to send error messages

    def __init__(self, task, **kwargs):
        """
        Initializes the worker thread.
        :param task: The task to perform ("embed" or "extract").
        :param kwargs: Arguments for the task function.
        """
        super().__init__()
        self.task = task
        self.kwargs = kwargs

    def run(self):
        """
        Executes the assigned task when the thread starts.
        """
        try:
            self.message.emit("Processing...") # Initial status message
            # Execute the specified task
            if self.task == "embed":
                # Call the embed_message function with provided arguments
                output_file = embed_message(
                    input_file=self.kwargs.get('input_file'),
                    output_file=self.kwargs.get('output_file'),
                    message=self.kwargs.get('message'),
                    alpha=self.kwargs.get('alpha', 0.001), # Default alpha if not provided
                    is_image=self.kwargs.get('is_image', False),
                    is_pdf=self.kwargs.get('is_pdf', False) # Pass is_pdf parameter
                )
                # Emit the result upon successful embedding
                self.result.emit({"status": "success", "output_file": output_file})

            elif self.task == "extract":
                # Call the extract_message function
                extracted_result = extract_message(self.kwargs.get('stego_file'))

                # Handle different result types (dictionary for new format, string for backward compatibility)
                if isinstance(extracted_result, dict):
                    self.result.emit({
                        "status": "success",
                        "message": extracted_result.get("message", ""),
                        "type": extracted_result.get("type", "text"), # Type of message (text, image, pdf)
                        "path": extracted_result.get("path", None)    # Path if file was saved (e.g., PDF)
                    })
                else:
                    # For backward compatibility if extract_message returns a string
                    self.result.emit({
                        "status": "success",
                        "message": extracted_result,
                        "type": "text" # Assume text if not specified
                    })

        except Exception as e:
            # Emit an error signal if any exception occurs
            self.error.emit(f"Error: {str(e)}")

class AudioStegoGUI(QMainWindow):
    """
    Main application window for the Audio Steganography tool.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Steganography with ECC, RSA and DWT")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create tabs for different functionalities
        self.tabs = QTabWidget()
        self.embed_tab = QWidget()
        self.extract_tab = QWidget()
        self.analysis_tab = QWidget()  # New analysis tab
        self.about_tab = QWidget()

        # Add tabs to the tab widget
        self.tabs.addTab(self.embed_tab, "Embed Message")
        self.tabs.addTab(self.extract_tab, "Extract Message")
        self.tabs.addTab(self.analysis_tab, "Analysis")  # Add the analysis tab
        self.tabs.addTab(self.about_tab, "About")

        self.layout.addWidget(self.tabs)

        # Setup UI for each tab
        self.setup_embed_tab()
        self.setup_extract_tab()
        self.setup_analysis_tab()  # Setup the analysis tab
        self.setup_about_tab()

        # Store report file path for the analysis tab
        self.current_report_path = None

    def setup_embed_tab(self):
        """Sets up the UI elements for the 'Embed Message' tab."""
        layout = QVBoxLayout(self.embed_tab)

        # Input file selection group
        input_group = QGroupBox("Audio Input")
        input_layout = QHBoxLayout()

        self.input_file_path = QLineEdit()
        self.input_file_path.setPlaceholderText("Select input audio file or leave empty for a sample file")

        browse_input_btn = QPushButton("Browse...")
        browse_input_btn.clicked.connect(self.browse_input_file)

        generate_sample_btn = QPushButton("Generate Sample")
        generate_sample_btn.clicked.connect(self.generate_sample_audio)

        input_layout.addWidget(self.input_file_path)
        input_layout.addWidget(browse_input_btn)
        input_layout.addWidget(generate_sample_btn)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Message type selection group (Text, Image, PDF)
        message_type_group = QGroupBox("Message Type")
        message_type_layout = QHBoxLayout()

        self.text_radio = QRadioButton("Text Message")
        self.image_radio = QRadioButton("Image File")
        self.pdf_radio = QRadioButton("PDF Document")  # Radio button for PDF
        self.text_radio.setChecked(True) # Default to text message

        message_type_layout.addWidget(self.text_radio)
        message_type_layout.addWidget(self.image_radio)
        message_type_layout.addWidget(self.pdf_radio)  # Add PDF radio to layout
        message_type_group.setLayout(message_type_layout)
        layout.addWidget(message_type_group)

        # Message input group (dynamic based on message type)
        message_group = QGroupBox("Message")
        message_layout = QVBoxLayout()

        # Text message input widget
        self.message_text = QTextEdit()
        self.message_text.setPlaceholderText("Enter your message here")

        # Image file selection widget
        self.image_layout = QHBoxLayout()
        self.image_path = QLineEdit()
        self.image_path.setPlaceholderText("Select image file")

        browse_image_btn = QPushButton("Browse...")
        browse_image_btn.clicked.connect(self.browse_image_file)

        self.image_layout.addWidget(self.image_path)
        self.image_layout.addWidget(browse_image_btn)

        # PDF file selection widget
        self.pdf_layout = QHBoxLayout()
        self.pdf_path = QLineEdit()
        self.pdf_path.setPlaceholderText("Select PDF document")

        browse_pdf_btn = QPushButton("Browse...")
        browse_pdf_btn.clicked.connect(self.browse_pdf_file)

        self.pdf_layout.addWidget(self.pdf_path)
        self.pdf_layout.addWidget(browse_pdf_btn)

        # Initially show text input, hide image and PDF inputs
        message_layout.addWidget(self.message_text)
        message_layout.addLayout(self.image_layout)
        message_layout.addLayout(self.pdf_layout)
        self.image_path.hide()
        browse_image_btn.hide() # Hide browse button for image initially
        self.pdf_path.hide()
        browse_pdf_btn.hide()   # Hide browse button for PDF initially

        # Connect radio buttons to toggle input visibility
        self.text_radio.toggled.connect(self.toggle_message_input)
        self.image_radio.toggled.connect(self.toggle_message_input)
        self.pdf_radio.toggled.connect(self.toggle_message_input)

        message_group.setLayout(message_layout)
        layout.addWidget(message_group)

        # Output file selection group
        output_group = QGroupBox("Output")
        output_layout = QHBoxLayout()

        self.output_file_path = QLineEdit()
        self.output_file_path.setPlaceholderText("Save output as (default: output/stego.wav)")

        browse_output_btn = QPushButton("Browse...")
        browse_output_btn.clicked.connect(self.browse_output_file)

        output_layout.addWidget(self.output_file_path)
        output_layout.addWidget(browse_output_btn)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Advanced settings group (e.g., Alpha value for DWT)
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QHBoxLayout()

        alpha_label = QLabel("Alpha value for DWT:")
        self.alpha_value = QDoubleSpinBox() # Spin box for float input
        self.alpha_value.setRange(0.0001, 0.01) # Min and max values for alpha
        self.alpha_value.setSingleStep(0.0001)  # Increment/decrement step
        self.alpha_value.setValue(0.001)        # Default alpha value
        self.alpha_value.setDecimals(4)         # Number of decimal places

        advanced_layout.addWidget(alpha_label)
        advanced_layout.addWidget(self.alpha_value)
        advanced_layout.addStretch() # Pushes elements to the left

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        # Progress bar for embedding process
        self.embed_progress = QProgressBar()
        layout.addWidget(self.embed_progress)

        # Log output group
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True) # Make log text non-editable

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Embed button
        self.embed_button = QPushButton("Embed Message")
        self.embed_button.clicked.connect(self.start_embed)
        layout.addWidget(self.embed_button)

    def setup_extract_tab(self):
        """Sets up the UI elements for the 'Extract Message' tab."""
        layout = QVBoxLayout(self.extract_tab)

        # Stego audio file selection group
        stego_group = QGroupBox("Stego Audio File")
        stego_layout = QHBoxLayout()

        self.stego_file_path = QLineEdit()
        self.stego_file_path.setPlaceholderText("Select stego audio file")

        browse_stego_btn = QPushButton("Browse...")
        browse_stego_btn.clicked.connect(self.browse_stego_file)

        stego_layout.addWidget(self.stego_file_path)
        stego_layout.addWidget(browse_stego_btn)
        stego_group.setLayout(stego_layout)
        layout.addWidget(stego_group)

        # Progress bar for extraction process
        self.extract_progress = QProgressBar()
        layout.addWidget(self.extract_progress)

        # Extracted message display group
        message_group = QGroupBox("Extracted Message")
        message_layout = QVBoxLayout()

        self.extracted_message = QTextEdit()
        self.extracted_message.setReadOnly(True) # Make extracted message non-editable

        message_layout.addWidget(self.extracted_message)
        message_group.setLayout(message_layout)
        layout.addWidget(message_group)

        # Extract button
        self.extract_button = QPushButton("Extract Message")
        self.extract_button.clicked.connect(self.start_extract)
        layout.addWidget(self.extract_button)

    def setup_about_tab(self):
        """Sets up the UI elements for the 'About' tab."""
        layout = QVBoxLayout(self.about_tab)
        layout.setContentsMargins(20, 20, 20, 20) # Add some padding
        layout.setSpacing(15) # Spacing between widgets

        # Main title
        title = QLabel("Audio Steganography with ECC, RSA and DWT")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Description
        desc = QLabel(
            "This application allows you to hide secret messages or images "
            "inside audio files using a combination of Discrete Wavelet Transform (DWT) "
            "for steganography and hybrid encryption with ECC and RSA for security."
        )
        desc.setWordWrap(True) # Allow text to wrap
        desc.setAlignment(Qt.AlignmentFlag.AlignJustify)
        desc.setFixedHeight(80) # Fixed height for description

        # Features section
        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout(features_group)

        features_text = QLabel(
            "• Hide text messages in audio files\n"
            "• Hide image files in audio files\n"
            "• Double-layer encryption using ECC and RSA\n"
            "• Adjustable DWT parameters for optimal hiding\n"
            "• Extract hidden messages from stego files\n"
            "• Generate sample audio for testing"
        )
        features_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        features_layout.addWidget(features_text)

        # Technical details section
        tech_group = QGroupBox("Technical Details")
        tech_layout = QVBoxLayout(tech_group)

        tech_text = QLabel(
            "This application uses the following technologies:\n\n"
            "• DWT (Discrete Wavelet Transform) for embedding data in frequency domain\n"
            "• ECC (Elliptic Curve Cryptography) for key exchange\n"
            "• RSA for asymmetric encryption of messages\n"
            "• PyQt6 for the graphical user interface\n"
            "• Base64 encoding for handling binary data"
        )
        tech_text.setWordWrap(True)
        tech_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        tech_layout.addWidget(tech_text)

        # Version and credits
        version = QLabel("Version 1.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        credits = QLabel("© 2025 - Audio Steganography Project - Kelompok 6")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add all widgets to main layout
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(features_group)
        layout.addWidget(tech_group)
        layout.addStretch(1) # Pushes version and credits to the bottom
        layout.addWidget(version)
        layout.addWidget(credits)

    def setup_analysis_tab(self):
        """Sets up the UI elements for the 'Analysis' tab."""
        layout = QVBoxLayout(self.analysis_tab)

        # Original audio file selection group
        original_group = QGroupBox("Original Audio")
        original_layout = QHBoxLayout()

        self.original_file_path = QLineEdit()
        self.original_file_path.setPlaceholderText("Select original audio file")

        browse_original_btn = QPushButton("Browse...")
        browse_original_btn.clicked.connect(self.browse_original_file)

        original_layout.addWidget(self.original_file_path)
        original_layout.addWidget(browse_original_btn)
        original_group.setLayout(original_layout)
        layout.addWidget(original_group)

        # Stego audio file selection group for analysis
        stego_analysis_group = QGroupBox("Stego Audio")
        stego_analysis_layout = QHBoxLayout()

        self.stego_analysis_file_path = QLineEdit()
        self.stego_analysis_file_path.setPlaceholderText("Select stego audio file")

        browse_stego_analysis_btn = QPushButton("Browse...")
        browse_stego_analysis_btn.clicked.connect(self.browse_stego_analysis_file)

        stego_analysis_layout.addWidget(self.stego_analysis_file_path)
        stego_analysis_layout.addWidget(browse_stego_analysis_btn)
        stego_analysis_group.setLayout(stego_analysis_layout)
        layout.addWidget(stego_analysis_group)

        # Message input for security analysis group
        security_group = QGroupBox("Security Analysis")
        security_layout = QVBoxLayout()

        message_layout = QHBoxLayout()
        message_label = QLabel("Message:")
        self.security_message = QLineEdit()
        self.security_message.setPlaceholderText("Enter a message to analyze security metrics")
        message_layout.addWidget(message_label)
        message_layout.addWidget(self.security_message)

        security_layout.addLayout(message_layout)
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)

        # Results display group
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(150) # Set a minimum height for the results area

        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Analysis buttons layout
        buttons_layout = QHBoxLayout()

        self.quality_button = QPushButton("Audio Quality Analysis")
        self.quality_button.clicked.connect(self.analyze_audio_quality)

        self.security_button = QPushButton("Security Analysis")
        self.security_button.clicked.connect(self.analyze_security)

        self.view_report_button = QPushButton("View Report")
        self.view_report_button.clicked.connect(self.view_report)
        self.view_report_button.setEnabled(False) # Initially disabled

        buttons_layout.addWidget(self.quality_button)
        buttons_layout.addWidget(self.security_button)
        buttons_layout.addWidget(self.view_report_button)

        layout.addLayout(buttons_layout)

    def toggle_message_input(self):
        """
        Switches the visibility of message input fields (text, image, PDF)
        based on the selected radio button.
        """
        # Hide all input fields and their browse buttons first
        self.message_text.hide()
        self.image_path.hide()
        self.pdf_path.hide()

        # Find and hide browse buttons associated with image and PDF paths
        # Assumes browse button is the only QPushButton in the parent layout of the QLineEdit
        for btn in self.image_path.parent().findChildren(QPushButton):
            btn.hide()
        for btn in self.pdf_path.parent().findChildren(QPushButton):
            btn.hide()

        # Show the input field and browse button for the selected message type
        if self.text_radio.isChecked():
            self.message_text.show()
        elif self.image_radio.isChecked():
            self.image_path.show()
            for btn in self.image_path.parent().findChildren(QPushButton):
                btn.show()
        elif self.pdf_radio.isChecked():
            self.pdf_path.show()
            for btn in self.pdf_path.parent().findChildren(QPushButton):
                btn.show()

    def browse_input_file(self):
        """Opens a file dialog to select an input audio file (.wav)."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.input_file_path.setText(file_path)

    def browse_image_file(self):
        """Opens a file dialog to select an image file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image_path.setText(file_path)

    def browse_pdf_file(self):
        """Opens a file dialog to select a PDF document."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF Document", "", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_path.setText(file_path)

    def browse_output_file(self):
        """Opens a file dialog to select a location to save the output stego audio file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output File", "", "Audio Files (*.wav)")
        if file_path:
            self.output_file_path.setText(file_path)

    def browse_stego_file(self):
        """Opens a file dialog to select a stego audio file for extraction."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Stego Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.stego_file_path.setText(file_path)

    def browse_original_file(self):
        """Opens a file dialog to select an original audio file for analysis."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Original Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.original_file_path.setText(file_path)

    def browse_stego_analysis_file(self):
        """Opens a file dialog to select a stego audio file for analysis."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Stego Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.stego_analysis_file_path.setText(file_path)

    def generate_sample_audio(self):
        """Generates a sample audio file for testing purposes."""
        from core import generate_audio # Import the audio generation function
        output_path = 'output/sample.wav' # Default path for sample audio
        os.makedirs('output', exist_ok=True) # Ensure 'output' directory exists

        self.log_text.append("Generating sample audio file...")
        generate_audio(output_path) # Call the generation function
        self.log_text.append(f"Sample audio generated: {output_path}")
        self.input_file_path.setText(output_path) # Set the input file path to the generated sample

    def log_message(self, message):
        """Appends a message to the log QTextEdit in the 'Embed' tab."""
        self.log_text.append(message)

    def start_embed(self):
        """
        Starts the embedding process. Validates inputs and runs the
        embedding task in a separate WorkerThread.
        """
        # Validate inputs based on selected message type
        if self.text_radio.isChecked():
            message = self.message_text.toPlainText()
            is_image = False
            is_pdf = False
            if not message:
                QMessageBox.warning(self, "Warning", "Please enter a message.")
                return
        elif self.image_radio.isChecked():
            message = self.image_path.text()
            is_image = True
            is_pdf = False
            if not message or not os.path.exists(message):
                QMessageBox.warning(self, "Warning", "Please select a valid image file.")
                return
        elif self.pdf_radio.isChecked():
            message = self.pdf_path.text()
            is_image = False
            is_pdf = True
            if not message or not os.path.exists(message):
                QMessageBox.warning(self, "Warning", "Please select a valid PDF document.")
                return
            if not message.lower().endswith('.pdf'): # Basic PDF file check
                QMessageBox.warning(self, "Warning", "The selected file is not a PDF document.")
                return
        else: # Should not happen if one radio is always checked
            QMessageBox.warning(self, "Warning", "Please select a message type.")
            return

        input_file = self.input_file_path.text() if self.input_file_path.text() else None
        output_file = self.output_file_path.text() if self.output_file_path.text() else None
        alpha = self.alpha_value.value()

        # Disable UI elements during processing
        self.embed_button.setEnabled(False)
        self.embed_progress.setValue(0)
        self.log_text.clear()
        self.log_text.append("Starting embed process...")

        # Create and start the worker thread for embedding
        self.worker = WorkerThread(
            "embed",
            input_file=input_file,
            output_file=output_file,
            message=message,
            alpha=alpha,
            is_image=is_image,
            is_pdf=is_pdf
        )
        self.worker.message.connect(self.log_message) # Connect worker message signal to log
        self.worker.error.connect(self.handle_error)   # Connect worker error signal
        self.worker.result.connect(self.handle_embed_result) # Connect worker result signal
        self.worker.start() # Start the thread

        # Simulate progress (actual progress would ideally come from the worker)
        # This is a simple UI feedback mechanism
        for i in range(101):
            self.embed_progress.setValue(i)
            QApplication.processEvents() # Allow UI to update
            time.sleep(0.03) # Short delay

    def start_extract(self):
        """
        Starts the extraction process. Validates inputs and runs the
        extraction task in a separate WorkerThread.
        """
        stego_file = self.stego_file_path.text()

        if not stego_file or not os.path.exists(stego_file):
            QMessageBox.warning(self, "Warning", "Please select a valid stego audio file.")
            return

        # Disable UI elements during processing
        self.extract_button.setEnabled(False)
        self.extract_progress.setValue(0)
        self.extracted_message.clear()

        # Create and start the worker thread for extraction
        self.worker = WorkerThread("extract", stego_file=stego_file)
        self.worker.result.connect(self.handle_extract_result) # Connect worker result signal
        self.worker.error.connect(self.handle_error)       # Connect worker error signal
        self.worker.start() # Start the thread

        # Simulate progress
        for i in range(101):
            self.extract_progress.setValue(i)
            QApplication.processEvents() # Allow UI to update
            time.sleep(0.03) # Short delay

    def handle_embed_result(self, result):
        """Handles the result from the embedding worker thread."""
        if result["status"] == "success":
            output_file = result["output_file"]

            if output_file:
                # Log success messages
                self.log_message(f"Message successfully embedded in: {output_file}")
                self.log_message(f"Keys saved in: {output_file}.key")
                self.log_message(f"Additional info: {output_file}.info")

                QMessageBox.information(
                    self,
                    "Success",
                    f"Message successfully embedded in:\n{output_file}"
                )
            else:
                self.log_message("Error: Embedding failed. Output file not generated.")
                QMessageBox.warning(self, "Error", "Embedding failed. Output file not generated.")

        self.embed_button.setEnabled(True) # Re-enable the embed button

    def handle_extract_result(self, result):
        """Handles the result from the extraction worker thread."""
        if result["status"] == "success":
            extracted_message = result["message"]
            message_type = result.get("type", "text") # Get message type (text, pdf, image)
            file_path_if_any = result.get("path", None) # Get path if a file was saved

            if extracted_message or file_path_if_any: # Check if there's content or a saved file
                if message_type == "pdf" and file_path_if_any:
                    self.extracted_message.setPlainText(f"[PDF document extracted]\nSaved to: {file_path_if_any}")
                    # Ask user if they want to open the extracted PDF
                    reply = QMessageBox.question(
                        self,
                        "PDF Document Extracted",
                        f"PDF document successfully extracted and saved to:\n{file_path_if_any}\n\nWould you like to open it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.open_file(file_path_if_any)

                elif message_type == "image":
                    # For images, typically the base64 data is in 'extracted_message'
                    self.extracted_message.setPlainText("[The extracted data appears to be an image]")
                    # Ask user if they want to save the extracted image
                    reply = QMessageBox.question(
                        self,
                        "Image Detected",
                        "The extracted data appears to be an image. Would you like to save it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.save_extracted_image(extracted_message) # Pass the base64 data
                else: # Default to text message
                    self.extracted_message.setPlainText(extracted_message)
            else:
                self.extracted_message.setPlainText("Error: Failed to extract message or message is empty.")
        else: # Should be handled by handle_error, but as a fallback
             self.extracted_message.setPlainText(f"Extraction failed: {result.get('message', 'Unknown error')}")


        self.extract_button.setEnabled(True) # Re-enable the extract button

    def open_file(self, file_path):
        """Opens a file using the default system application."""
        if file_path and os.path.exists(file_path):
            import subprocess # For running external commands
            # import sys # Already imported

            try:
                if sys.platform.startswith('darwin'):  # macOS
                    subprocess.call(('open', file_path))
                elif sys.platform.startswith('win'):  # Windows
                    os.startfile(file_path) # More direct way for Windows
                else:  # Linux and other Unix-like
                    subprocess.call(('xdg-open', file_path))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "File not found or path is invalid.")

    def save_extracted_image(self, base64_data):
        """
        Decodes base64 image data and prompts the user to save it as an image file.
        :param base64_data: The base64 encoded string of the image.
        """
        try:
            import base64     # For base64 decoding
            from PIL import Image # For image manipulation (Pillow library)
            import io         # For handling byte streams

            # Handle potential "data:image/png;base64," prefix
            if base64_data.startswith("data:image"):
                base64_data = base64_data.split(",")[1] # Get the actual base64 part

            # Decode the base64 data
            image_data = base64.b64decode(base64_data)

            # Create an image object from the decoded bytes
            image = Image.open(io.BytesIO(image_data))

            # Ask user where to save the image
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                "output/extracted_image.png", # Default save path and name
                "Images (*.png *.jpg *.bmp)" # File type filter
            )

            if file_path:
                image.save(file_path) # Save the image
                QMessageBox.information(
                    self,
                    "Success",
                    f"Image successfully saved to:\n{file_path}"
                )
        except ImportError:
            QMessageBox.warning(self, "Error", "Pillow library is not installed. Cannot save image.")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to save image: {str(e)}"
            )

    def handle_error(self, error_message):
        """Handles errors emitted from the worker thread."""
        self.log_message(error_message) # Log the error in the embed tab's log
        # Also display error in extract tab if that was the source (or a general popup)
        self.extracted_message.append(f"\nError: {error_message}") # Append to extract tab as well for visibility
        self.embed_button.setEnabled(True)    # Re-enable embed button
        self.extract_button.setEnabled(True)  # Re-enable extract button
        QMessageBox.warning(self, "Error", error_message) # Show a popup error message

    def analyze_audio_quality(self):
        """Performs audio quality analysis between an original and a stego file."""
        try:
            from utils.metrics import generate_quality_report # Import on demand
        except ImportError:
            QMessageBox.critical(self, "Error", "Metrics utility not found. Cannot perform analysis.")
            return

        original_file = self.original_file_path.text()
        stego_file = self.stego_analysis_file_path.text()

        # Validate input files
        if not original_file or not os.path.exists(original_file):
            QMessageBox.warning(self, "Warning", "Please select a valid original audio file.")
            return
        if not stego_file or not os.path.exists(stego_file):
            QMessageBox.warning(self, "Warning", "Please select a valid stego audio file.")
            return

        try:
            self.results_text.clear()
            self.results_text.append("Analyzing audio quality...")
            QApplication.processEvents() # Update UI

            # Generate quality report using the metrics utility
            metrics = generate_quality_report(original_file, stego_file)

            # Display results in the text area
            self.results_text.append(f"\nQuality Metrics:")
            self.results_text.append(f"- Mean Square Error (MSE): {metrics['mse']:.6f}")
            self.results_text.append(f"- Peak Signal-to-Noise Ratio (PSNR): {metrics['psnr']:.2f} dB")
            self.results_text.append(f"- Structural Similarity Index (SSIM): {metrics['ssim']:.6f}")
            self.results_text.append(f"\nQuality Report saved to: {metrics['report_file']}")

            # Enable view report button and store path
            self.current_report_path = metrics['report_file']
            self.view_report_button.setEnabled(True)

        except Exception as e:
            self.results_text.append(f"\nError during quality analysis: {str(e)}")
            QMessageBox.warning(self, "Error", f"Quality analysis failed: {str(e)}")
            self.view_report_button.setEnabled(False)

    def analyze_security(self):
        """Performs security analysis on a given message (e.g., Avalanche Effect)."""
        try:
            from utils.metrics import analyze_security as analyze_sec # Import on demand
        except ImportError:
            QMessageBox.critical(self, "Error", "Metrics utility not found. Cannot perform analysis.")
            return

        message = self.security_message.text()

        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a message for security analysis.")
            return

        try:
            self.results_text.clear()
            self.results_text.append("Analyzing security metrics...")
            QApplication.processEvents() # Update UI

            # Perform security analysis using the metrics utility
            metrics = analyze_sec(message)

            # Display results
            self.results_text.append(f"\nSecurity Metrics:")
            self.results_text.append(f"- Avalanche Effect: {metrics['avalanche_effect']:.2f}%")
            # Display average and std dev if available (depends on analyze_sec implementation)
            if 'avg_avalanche' in metrics:
                self.results_text.append(f"- Average Avalanche Effect: {metrics['avg_avalanche']:.2f}%")
                self.results_text.append(f"- Standard Deviation of Avalanche: {metrics['std_avalanche']:.2f}%")

            if metrics.get('report_file'): # Check if a report file was generated
                self.results_text.append(f"\nSecurity Report saved to: {metrics['report_file']}")
                self.current_report_path = metrics['report_file']
                self.view_report_button.setEnabled(True)
            else:
                self.view_report_button.setEnabled(False)

        except Exception as e:
            self.results_text.append(f"\nError during security analysis: {str(e)}")
            QMessageBox.warning(self, "Error", f"Security analysis failed: {str(e)}")
            self.view_report_button.setEnabled(False)

    def view_report(self):
        """Opens the currently stored report file using the default system application."""
        if self.current_report_path and os.path.exists(self.current_report_path):
            self.open_file(self.current_report_path) # Use the existing open_file method
        else:
            QMessageBox.warning(self, "Error", "Report file not found or no report generated yet.")

def run_gui():
    """Initializes and runs the PyQt6 application."""
    app = QApplication(sys.argv) # Create a QApplication instance
    window = AudioStegoGUI()    # Create an instance of the main window
    window.show()               # Show the window
    sys.exit(app.exec())        # Start the application's event loop

if __name__ == "__main__":
    # This block executes if the script is run directly
    run_gui()
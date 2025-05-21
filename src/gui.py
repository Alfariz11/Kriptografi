# src/gui.py
import sys
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                            QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTextEdit, QFileDialog, QProgressBar, QRadioButton, 
                            QGroupBox, QLineEdit, QMessageBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap

from core import embed_message, extract_message

class WorkerThread(QThread):
    """Worker thread for long-running tasks to keep the UI responsive"""
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    result = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, task, **kwargs):
        super().__init__()
        self.task = task
        self.kwargs = kwargs
    
    def run(self):
        try:
            self.message.emit("Processing...")
            # Execute the task
            if self.task == "embed":
                output_file = embed_message(
                    input_file=self.kwargs.get('input_file'),
                    output_file=self.kwargs.get('output_file'),
                    message=self.kwargs.get('message'),
                    alpha=self.kwargs.get('alpha', 0.001),
                    is_image=self.kwargs.get('is_image', False)
                )
                self.result.emit({"status": "success", "output_file": output_file})
            
            elif self.task == "extract":
                extracted_message = extract_message(self.kwargs.get('stego_file'))
                self.result.emit({"status": "success", "message": extracted_message})
                
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

class AudioStegoGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Steganography with ECC, RSA and DWT")
        self.setGeometry(100, 100, 800, 600)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.embed_tab = QWidget()
        self.extract_tab = QWidget()
        self.analysis_tab = QWidget()  # New analysis tab
        self.about_tab = QWidget()
        
        self.tabs.addTab(self.embed_tab, "Embed Message")
        self.tabs.addTab(self.extract_tab, "Extract Message")
        self.tabs.addTab(self.analysis_tab, "Analysis")  # Add the analysis tab
        self.tabs.addTab(self.about_tab, "About")
        
        self.layout.addWidget(self.tabs)
        
        # Setup each tab
        self.setup_embed_tab()
        self.setup_extract_tab()
        self.setup_analysis_tab()  # Setup the analysis tab
        self.setup_about_tab()
        
        # Store report file path
        self.current_report_path = None

    def setup_embed_tab(self):
        layout = QVBoxLayout(self.embed_tab)
        
        # Input file selection
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
        
        # Message type selection
        message_type_group = QGroupBox("Message Type")
        message_type_layout = QHBoxLayout()
        
        self.text_radio = QRadioButton("Text Message")
        self.image_radio = QRadioButton("Image File")
        self.text_radio.setChecked(True)
        
        message_type_layout.addWidget(self.text_radio)
        message_type_layout.addWidget(self.image_radio)
        message_type_group.setLayout(message_type_layout)
        layout.addWidget(message_type_group)
        
        # Message input
        message_group = QGroupBox("Message")
        message_layout = QVBoxLayout()
        
        # Text message widget
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
        
        # Initially show text input, hide image input
        message_layout.addWidget(self.message_text)
        message_layout.addLayout(self.image_layout)
        self.image_path.hide()
        browse_image_btn.hide()
        
        # Connect radio buttons to switch between message input types
        self.text_radio.toggled.connect(self.toggle_message_input)
        
        message_group.setLayout(message_layout)
        layout.addWidget(message_group)
        
        # Output file selection
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
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QHBoxLayout()
        
        alpha_label = QLabel("Alpha value for DWT:")
        self.alpha_value = QDoubleSpinBox()
        self.alpha_value.setRange(0.0001, 0.01)
        self.alpha_value.setSingleStep(0.0001)
        self.alpha_value.setValue(0.001)
        self.alpha_value.setDecimals(4)
        
        advanced_layout.addWidget(alpha_label)
        advanced_layout.addWidget(self.alpha_value)
        advanced_layout.addStretch()
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Progress bar
        self.embed_progress = QProgressBar()
        layout.addWidget(self.embed_progress)
        
        # Log output
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Embed button
        self.embed_button = QPushButton("Embed Message")
        self.embed_button.clicked.connect(self.start_embed)
        layout.addWidget(self.embed_button)
    
    def setup_extract_tab(self):
        layout = QVBoxLayout(self.extract_tab)
        
        # Stego file selection
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
        
        # Progress bar
        self.extract_progress = QProgressBar()
        layout.addWidget(self.extract_progress)
        
        # Extracted message display
        message_group = QGroupBox("Extracted Message")
        message_layout = QVBoxLayout()
        
        self.extracted_message = QTextEdit()
        self.extracted_message.setReadOnly(True)
        
        message_layout.addWidget(self.extracted_message)
        message_group.setLayout(message_layout)
        layout.addWidget(message_group)
        
        # Extract button
        self.extract_button = QPushButton("Extract Message")
        self.extract_button.clicked.connect(self.start_extract)
        layout.addWidget(self.extract_button)
    
    def setup_about_tab(self):
        layout = QVBoxLayout(self.about_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
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
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignJustify)
        desc.setFixedHeight(80)
        
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
        layout.addStretch(1)
        layout.addWidget(version)
        layout.addWidget(credits)
    
    def setup_analysis_tab(self):
        layout = QVBoxLayout(self.analysis_tab)
        
        # Original file selection
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
        
        # Stego file selection
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
        
        # Message input for security analysis
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
        
        # Results display
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(150)
        
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Analysis buttons
        buttons_layout = QHBoxLayout()
        
        self.quality_button = QPushButton("Audio Quality Analysis")
        self.quality_button.clicked.connect(self.analyze_audio_quality)
        
        self.security_button = QPushButton("Security Analysis")
        self.security_button.clicked.connect(self.analyze_security)
        
        self.view_report_button = QPushButton("View Report")
        self.view_report_button.clicked.connect(self.view_report)
        self.view_report_button.setEnabled(False)
        
        buttons_layout.addWidget(self.quality_button)
        buttons_layout.addWidget(self.security_button)
        buttons_layout.addWidget(self.view_report_button)
        
        layout.addLayout(buttons_layout)
    
    def toggle_message_input(self):
        """Switch between text and image message input"""
        if self.text_radio.isChecked():
            self.message_text.show()
            self.image_path.hide()
            self.image_path.parent().findChild(QPushButton, "").hide()
        else:
            self.message_text.hide()
            self.image_path.show()
            for btn in self.image_path.parent().findChildren(QPushButton):
                btn.show()
    
    def browse_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.input_file_path.setText(file_path)
    
    def browse_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image_path.setText(file_path)
    
    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output File", "", "Audio Files (*.wav)")
        if file_path:
            self.output_file_path.setText(file_path)
    
    def browse_stego_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Stego Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.stego_file_path.setText(file_path)
    
    def browse_original_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Original Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.original_file_path.setText(file_path)
    
    def browse_stego_analysis_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Stego Audio File", "", "Audio Files (*.wav)")
        if file_path:
            self.stego_analysis_file_path.setText(file_path)
    
    def generate_sample_audio(self):
        # Default path for sample audio
        from core import generate_audio
        output_path = 'output/sample.wav'
        os.makedirs('output', exist_ok=True)
        
        self.log_text.append("Generating sample audio file...")
        generate_audio(output_path)
        self.log_text.append(f"Sample audio generated: {output_path}")
        self.input_file_path.setText(output_path)
    
    def log_message(self, message):
        """Add message to the log text box"""
        self.log_text.append(message)
    
    def start_embed(self):
        """Start the embed process in a separate thread"""
        # Validate inputs
        if self.text_radio.isChecked():
            message = self.message_text.toPlainText()
            is_image = False
            if not message:
                QMessageBox.warning(self, "Warning", "Please enter a message.")
                return
        else:
            message = self.image_path.text()
            is_image = True
            if not message or not os.path.exists(message):
                QMessageBox.warning(self, "Warning", "Please select a valid image file.")
                return
        
        input_file = self.input_file_path.text() if self.input_file_path.text() else None
        output_file = self.output_file_path.text() if self.output_file_path.text() else None
        alpha = self.alpha_value.value()
        
        # Disable the button and show progress
        self.embed_button.setEnabled(False)
        self.embed_progress.setValue(0)
        self.log_text.clear()
        self.log_text.append("Starting embed process...")
        
        # Create and start the worker thread
        self.worker = WorkerThread(
            "embed", 
            input_file=input_file,
            output_file=output_file,
            message=message,
            alpha=alpha,
            is_image=is_image
        )
        self.worker.message.connect(self.log_message)
        self.worker.error.connect(self.handle_error)
        self.worker.result.connect(self.handle_embed_result)
        self.worker.start()
        
        # Simulate progress
        for i in range(101):
            self.embed_progress.setValue(i)
            QApplication.processEvents()
            time.sleep(0.03)
    
    def start_extract(self):
        """Start the extract process in a separate thread"""
        stego_file = self.stego_file_path.text()
        
        if not stego_file or not os.path.exists(stego_file):
            QMessageBox.warning(self, "Warning", "Please select a valid stego audio file.")
            return
        
        # Disable the button and show progress
        self.extract_button.setEnabled(False)
        self.extract_progress.setValue(0)
        self.extracted_message.clear()
        
        # Create and start the worker thread
        self.worker = WorkerThread("extract", stego_file=stego_file)
        self.worker.result.connect(self.handle_extract_result)
        self.worker.error.connect(self.handle_error)
        self.worker.start()
        
        # Simulate progress
        for i in range(101):
            self.extract_progress.setValue(i)
            QApplication.processEvents()
            time.sleep(0.03)
    
    def handle_embed_result(self, result):
        """Handle the result from the embed thread"""
        if result["status"] == "success":
            output_file = result["output_file"]
            
            if output_file:
                self.log_message(f"Message successfully embedded in: {output_file}")
                self.log_message(f"Keys saved in: {output_file}.key")
                self.log_message(f"Additional info: {output_file}.info")
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Message successfully embedded in:\n{output_file}"
                )
            else:
                self.log_message("Error: Embedding failed.")
        
        self.embed_button.setEnabled(True)
    
    def handle_extract_result(self, result):
        """Handle the result from the extract thread"""
        if result["status"] == "success":
            extracted_message = result["message"]
            
            if extracted_message:
                # Check if it might be base64-encoded image
                if extracted_message.startswith("data:image") or (
                    len(extracted_message) > 100 and 
                    all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" 
                        for c in extracted_message[:100])
                ):
                    self.extracted_message.setPlainText("[The extracted data appears to be an image]")
                    
                    # Ask if user wants to save the image
                    reply = QMessageBox.question(
                        self, 
                        "Image Detected", 
                        "The extracted data appears to be an image. Would you like to save it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.save_extracted_image(extracted_message)
                else:
                    self.extracted_message.setPlainText(extracted_message)
            else:
                self.extracted_message.setPlainText("Error: Failed to extract message or message is empty.")
        
        self.extract_button.setEnabled(True)
    
    def save_extracted_image(self, base64_data):
        """Save the extracted base64 image to a file"""
        try:
            import base64
            from PIL import Image
            import io
            
            # Handle different base64 formats
            if base64_data.startswith("data:image"):
                # Extract the actual base64 data
                base64_data = base64_data.split(",")[1]
            
            # Decode the base64 data
            image_data = base64.b64decode(base64_data)
            
            # Create an image from the raw data
            image = Image.open(io.BytesIO(image_data))
            
            # Ask user where to save the image
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Image", 
                "output/extracted_image.png", 
                "Images (*.png *.jpg *.bmp)"
            )
            
            if file_path:
                image.save(file_path)
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Image successfully saved to:\n{file_path}"
                )
        except Exception as e:
            QMessageBox.warning(
                self, 
                "Error", 
                f"Failed to save image: {str(e)}"
            )
    
    def handle_error(self, error_message):
        """Handle error from the worker thread"""
        self.log_message(error_message)
        self.embed_button.setEnabled(True)
        self.extract_button.setEnabled(True)
        QMessageBox.warning(self, "Error", error_message)

    def analyze_audio_quality(self):
        from utils.metrics import generate_quality_report
        
        original_file = self.original_file_path.text()
        stego_file = self.stego_analysis_file_path.text()
        
        if not original_file or not os.path.exists(original_file):
            QMessageBox.warning(self, "Warning", "Please select a valid original audio file.")
            return
        
        if not stego_file or not os.path.exists(stego_file):
            QMessageBox.warning(self, "Warning", "Please select a valid stego audio file.")
            return
        
        try:
            self.results_text.clear()
            self.results_text.append("Analyzing audio quality...")
            
            # Generate quality report
            metrics = generate_quality_report(original_file, stego_file)
            
            # Display results
            self.results_text.append(f"\nQuality Metrics:")
            self.results_text.append(f"- Mean Square Error (MSE): {metrics['mse']:.6f}")
            self.results_text.append(f"- Peak Signal-to-Noise Ratio (PSNR): {metrics['psnr']:.2f} dB")
            self.results_text.append(f"- Structural Similarity Index (SSIM): {metrics['ssim']:.6f}")
            self.results_text.append(f"\nQuality Report saved to: {metrics['report_file']}")
            
            # Enable view report button
            self.current_report_path = metrics['report_file']
            self.view_report_button.setEnabled(True)
            
        except Exception as e:
            self.results_text.append(f"\nError: {str(e)}")
            QMessageBox.warning(self, "Error", f"Analysis failed: {str(e)}")

    def analyze_security(self):
        from utils.metrics import analyze_security as analyze_sec
        
        message = self.security_message.text()
        
        if not message:
            QMessageBox.warning(self, "Warning", "Please enter a message for security analysis.")
            return
        
        try:
            self.results_text.clear()
            self.results_text.append("Analyzing security metrics...")
            
            # Generate security analysis
            metrics = analyze_sec(message)
            
            # Display results
            self.results_text.append(f"\nSecurity Metrics:")
            self.results_text.append(f"- Avalanche Effect: {metrics['avalanche_effect']:.2f}%")
            if 'avg_avalanche' in metrics:
                self.results_text.append(f"- Average Avalanche Effect: {metrics['avg_avalanche']:.2f}%")
                self.results_text.append(f"- Standard Deviation: {metrics['std_avalanche']:.2f}%")
            
            if metrics['report_file']:
                self.results_text.append(f"\nSecurity Report saved to: {metrics['report_file']}")
                self.current_report_path = metrics['report_file']
                self.view_report_button.setEnabled(True)
            else:
                self.view_report_button.setEnabled(False)
            
        except Exception as e:
            self.results_text.append(f"\nError: {str(e)}")
            QMessageBox.warning(self, "Error", f"Analysis failed: {str(e)}")

    def view_report(self):
        if self.current_report_path and os.path.exists(self.current_report_path):
            # Open the report using the default system application
            import subprocess
            import sys
            
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.call(('open', self.current_report_path))
            elif sys.platform.startswith('win'):  # Windows
                os.startfile(self.current_report_path)
            else:  # Linux
                subprocess.call(('xdg-open', self.current_report_path))
        else:
            QMessageBox.warning(self, "Error", "Report file not found.")

def run_gui():
    app = QApplication(sys.argv)
    window = AudioStegoGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_gui()
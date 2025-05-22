# main.py
import sys  # For system-specific parameters and functions, like sys.path and sys.exit
import argparse  # For parsing command-line arguments
import os  # For interacting with the operating system, like path manipulation

# Add parent directory to sys.path
# This allows the script to import modules from the parent directory (e.g., the 'src' folder)
# when main.py is executed directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == "__main__":
    # Create an ArgumentParser object to handle command-line arguments
    parser = argparse.ArgumentParser(description="Audio Steganography with ECC, RSA and DWT")
    
    # Define command-line arguments
    parser.add_argument("--cli", action="store_true", help="Run in command-line interface mode")
    parser.add_argument("--embed", action="store_true", help="Embed message in audio file")
    parser.add_argument("--extract", action="store_true", help="Extract message from audio file")
    parser.add_argument("--input", type=str, help="Input audio file path (for embedding or extraction)")
    parser.add_argument("--output", type=str, help="Output audio file path (for embedding)")
    parser.add_argument("--message", type=str, help="Text message to embed")
    parser.add_argument("--image", type=str, help="Image file path to embed")
    parser.add_argument("--pdf", type=str, help="PDF document path to embed")
    parser.add_argument("--alpha", type=float, default=0.001, help="Alpha value for DWT (embedding strength, default: 0.001)")
    
    # Parse the command-line arguments provided by the user
    args = parser.parse_args()
    
    # --- Direct Command-line Embedding/Extraction ---
    # If --embed or --extract flag is used, perform the action directly without launching CLI or GUI.
    if args.embed or args.extract:
        # Import core steganography functions only when needed
        from src.core import embed_message, extract_message
        
        if args.embed:
            # Determine if the message to embed is an image or a PDF
            is_image = args.image is not None
            is_pdf = args.pdf is not None
            
            # Prioritize message source: text, then image, then PDF
            message = args.message
            if is_image:
                message = args.image  # Use image path as message
            elif is_pdf:
                message = args.pdf    # Use PDF path as message
            
            # Call the embedding function from src.core
            result = embed_message(
                input_file=args.input,
                output_file=args.output,
                message=message,
                alpha=args.alpha,
                is_image=is_image,
                is_pdf=is_pdf
            )
            
            # Print result of embedding
            if result:
                print(f"Message successfully embedded in: {result}")
                print(f"Keys saved in: {result}.key") # Key file for decryption
                print(f"Additional info: {result}.info") # Info file for metadata
            else:
                print("Embedding failed.")
                
        elif args.extract:
            # Ensure input file is provided for extraction
            if not args.input:
                print("Error: --input argument is required for extraction")
                sys.exit(1) # Exit with an error code
                
            # Call the extraction function from src.core
            result = extract_message(args.input)
            
            # Handle the extracted result
            if isinstance(result, dict): # Modern result format (dictionary)
                print("Message successfully extracted:")
                if result.get('type') == 'pdf':
                    pdf_path = result.get('path')
                    if pdf_path:
                        print(f"PDF document saved to: {pdf_path}")
                elif result.get('type') == 'image':
                    # For images, we might just confirm extraction or provide path if saved
                    print("[Image data detected]") # Or print image path if saved by extract_message
                else: # Default to text message
                    message = result.get('message', '')
                    # Print a preview of long messages
                    print(message[:100] + "..." if len(message) > 100 else message)
            else:
                # Backward compatibility for older versions where extract_message might return a string directly
                print(result)
                
        sys.exit(0) # Exit successfully after direct embed/extract operation
    
    # --- Regular Application Modes (CLI or GUI) ---
    # If --embed or --extract were not used, proceed to CLI or GUI mode.
    
    if args.cli:
        # Run in Command-Line Interface (CLI) mode
        from src.cli import main as cli_main # Import CLI main function
        cli_main() # Start the CLI
    else:
        # Run in Graphical User Interface (GUI) mode (default behavior if no specific mode is chosen)
        from src.gui import run_gui # Import GUI runner function
        run_gui() # Start the GUI
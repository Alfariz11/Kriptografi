# main.py
import sys
import argparse
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Steganography with ECC, RSA and DWT")
    parser.add_argument("--cli", action="store_true", help="Run in command-line interface mode")
    parser.add_argument("--embed", action="store_true", help="Embed message in audio file")
    parser.add_argument("--extract", action="store_true", help="Extract message from audio file")
    parser.add_argument("--input", type=str, help="Input audio file path")
    parser.add_argument("--output", type=str, help="Output audio file path")
    parser.add_argument("--message", type=str, help="Text message to embed")
    parser.add_argument("--image", type=str, help="Image file path to embed")
    parser.add_argument("--pdf", type=str, help="PDF document path to embed")
    parser.add_argument("--alpha", type=float, default=0.001, help="Alpha value for DWT (default: 0.001)")
    
    args = parser.parse_args()
    
    # Command line with arguments
    if args.embed or args.extract:
        from src.core import embed_message, extract_message
        
        if args.embed:
            is_image = args.image is not None
            is_pdf = args.pdf is not None
            
            message = args.message
            if is_image:
                message = args.image
            elif is_pdf:
                message = args.pdf
            
            result = embed_message(
                input_file=args.input,
                output_file=args.output,
                message=message,
                alpha=args.alpha,
                is_image=is_image,
                is_pdf=is_pdf
            )
            
            if result:
                print(f"Message successfully embedded in: {result}")
                print(f"Keys saved in: {result}.key")
                print(f"Additional info: {result}.info")
            else:
                print("Embedding failed.")
                
        elif args.extract:
            if not args.input:
                print("Error: --input argument is required for extraction")
                sys.exit(1)
                
            result = extract_message(args.input)
            
            if isinstance(result, dict):
                print("Message successfully extracted:")
                if result.get('type') == 'pdf':
                    pdf_path = result.get('path')
                    if pdf_path:
                        print(f"PDF document saved to: {pdf_path}")
                elif result.get('type') == 'image':
                    print("[Image data detected]")
                else:
                    message = result.get('message', '')
                    print(message[:100] + "..." if len(message) > 100 else message)
            else:
                # Backward compatibility
                print(result)
                
        sys.exit(0)
    
    # Regular modes (CLI or GUI)
    if args.cli:
        # CLI mode
        from src.cli import main as cli_main
        cli_main()
    else:
        # GUI mode (default)
        from src.gui import run_gui
        run_gui()
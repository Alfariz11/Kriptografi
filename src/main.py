# main.py
import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Steganography with ECC, RSA and DWT")
    parser.add_argument("--cli", action="store_true", help="Run in command-line interface mode")
    
    args = parser.parse_args()
    
    if args.cli:
        # CLI mode
        from cli import main as cli_main
        cli_main()
    else:
        # GUI mode (default)
        from gui import run_gui
        run_gui()
from core import embed_message, extract_message  # Import core steganography functions
import time  # For time-related functions, like sleep for animations
import os  # For operating system dependent functionality, like clearing the screen

# ANSI color codes for styling terminal output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"  # Resets the color to default

def clear_screen():
    """Clears the terminal screen."""
    # 'cls' for Windows, 'clear' for Linux/macOS
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation(text="Processing", duration=3):
    """Displays a simple loading animation in the terminal."""
    for i in range(duration * 2): # Iterate more times for a smoother feel with 0.5s sleep
        # Print the text followed by a cycling number of dots
        print(f"{YELLOW}{text}{'.' * (i % 3 + 1)}{RESET}", end='\r') # '\r' returns cursor to line start
        time.sleep(0.5)
    # Clear the loading animation line after completion
    print(" " * (len(text) + 4), end='\r')

def main():
    """Main function to run the CLI application."""
    clear_screen()
    while True:
        # Display the main menu
        print(f"{BLUE}{'='*60}")
        print("     AUDIO STEGANOGRAPHY WITH ECC, RSA ENCRYPTION")
        print("                    AND DWT TRANSFORM")
        print("="*60 + RESET)
        print(f"{GREEN}1.{RESET} Embed text message into audio file")
        print(f"{GREEN}2.{RESET} Embed image into audio file")
        print(f"{GREEN}3.{RESET} Embed PDF document into audio file") # Added PDF option
        print(f"{GREEN}4.{RESET} Extract message from audio file")
        print(f"{GREEN}5.{RESET} Exit")

        choice = input(f"\n{YELLOW}Select an option (1-5): {RESET}")

        if choice == '1': # Embed text message
            clear_screen()
            print(f"{BLUE}--- Embed Text Message ---{RESET}")
            message_text = input(f"{YELLOW}Enter text message: {RESET}")
            # Get optional input/output file paths and alpha
            input_audio = input(f"{YELLOW}Enter input audio file path (e.g., input/source.wav) [or press Enter for sample]: {RESET}")
            output_audio = input(f"{YELLOW}Enter output stego audio file path (e.g., output/stego_text.wav) [or press Enter for default]: {RESET}")
            alpha_str = input(f"{YELLOW}Enter DWT alpha value (e.g., 0.001) [or press Enter for default]: {RESET}")
            alpha_val = float(alpha_str) if alpha_str else None

            loading_animation("Embedding message")
            result_path = embed_message(
                input_file=input_audio if input_audio else None,
                output_file=output_audio if output_audio else None,
                message=message_text,
                alpha=alpha_val if alpha_val is not None else 0.001 # Pass None to use function's default or the value
            )
            if result_path:
                print(f"{GREEN}Text message embedded successfully: {result_path}{RESET}")
            else:
                print(f"{RED}Failed to embed text message.{RESET}")


        elif choice == '2': # Embed image
            clear_screen()
            print(f"{BLUE}--- Embed Image ---{RESET}")
            image_path = input(f"{YELLOW}Enter image path (e.g., input/photo.png): {RESET}")
            input_audio = input(f"{YELLOW}Enter input audio file path [or press Enter for sample]: {RESET}")
            output_audio = input(f"{YELLOW}Enter output stego audio file path (e.g., output/stego_image.wav) [or press Enter for default]: {RESET}")
            alpha_str = input(f"{YELLOW}Enter DWT alpha value [or press Enter for default]: {RESET}")
            alpha_val = float(alpha_str) if alpha_str else None

            loading_animation("Processing image and embedding")
            try:
                result_path = embed_message(
                    input_file=input_audio if input_audio else None,
                    output_file=output_audio if output_audio else None,
                    message=image_path,
                    is_image=True,
                    alpha=alpha_val if alpha_val is not None else 0.001
                )
                if result_path:
                    print(f"{GREEN}Image embedded successfully: {result_path}{RESET}")
                else:
                    print(f"{RED}Failed to embed image.{RESET}")
            except FileNotFoundError:
                print(f"{RED}[ERROR] Image file not found at: {image_path}{RESET}")
            except Exception as e:
                print(f"{RED}[ERROR] {e}{RESET}")

        elif choice == '3': # Embed PDF document
            clear_screen()
            print(f"{BLUE}--- Embed PDF Document ---{RESET}")
            pdf_path = input(f"{YELLOW}Enter PDF document path (e.g., input/mydoc.pdf): {RESET}")
            input_audio = input(f"{YELLOW}Enter input audio file path [or press Enter for sample]: {RESET}")
            output_audio = input(f"{YELLOW}Enter output stego audio file path (e.g., output/stego_pdf.wav) [or press Enter for default]: {RESET}")
            alpha_str = input(f"{YELLOW}Enter DWT alpha value [or press Enter for default]: {RESET}")
            alpha_val = float(alpha_str) if alpha_str else None

            loading_animation("Processing PDF document and embedding")
            try:
                result_path = embed_message(
                    input_file=input_audio if input_audio else None,
                    output_file=output_audio if output_audio else None,
                    message=pdf_path,
                    is_pdf=True,
                    alpha=alpha_val if alpha_val is not None else 0.001
                )
                if result_path:
                    print(f"{GREEN}PDF document embedded successfully: {result_path}{RESET}")
                else:
                    print(f"{RED}Failed to embed PDF document.{RESET}")
            except FileNotFoundError:
                print(f"{RED}[ERROR] PDF file not found at: {pdf_path}{RESET}")
            except Exception as e:
                print(f"{RED}[ERROR] {e}{RESET}")

        elif choice == '4': # Extract message
            clear_screen()
            print(f"{BLUE}--- Extract Message ---{RESET}")
            stego_audio_path = input(f"{YELLOW}Enter path to stego audio file (e.g., output/stego.wav): {RESET}")
            print(f"{YELLOW}Extracting message from audio file...{RESET}")
            loading_animation("Extracting data")
            extracted_result = extract_message(stego_file=stego_audio_path if stego_audio_path else None)

            if extracted_result:
                print(f"\n{GREEN}Message extracted successfully:{RESET}")
                if isinstance(extracted_result, dict): # Modern dictionary result
                    msg_type = extracted_result.get('type', 'text')
                    msg_content = extracted_result.get('message', '')
                    msg_path = extracted_result.get('path')

                    if msg_type == 'pdf' and msg_path:
                        print(f"{GREEN}PDF document extracted and saved to: {msg_path}{RESET}")
                    elif msg_type == 'image':
                        # The CLI might not display the image, but confirms detection.
                        # GUI would handle saving/displaying.
                        print(f"{GREEN}[Image data detected. Message content (base64 preview): {msg_content[:60]}...]{RESET}")
                        print(f"{YELLOW}To save the image, use the GUI or a script to decode the base64 data.{RESET}")
                    else: # Text or other JSON
                        print(f"{BLUE}Type: {msg_type.upper()}{RESET}")
                        print(f"{msg_content[:200] + '...' if len(msg_content) > 200 else msg_content}")
                else: # Backward compatibility for string result
                    print(f"{extracted_result[:200] + '...' if len(extracted_result) > 200 else extracted_result}")
            else:
                print(f"{RED}Failed to extract message or message is empty.{RESET}")

        elif choice == '5': # Exit
            print(f"{BLUE}\nExiting program. Thank you for using this application!{RESET}")
            break

        else: # Invalid choice
            print(f"{RED}Invalid option. Please choose between 1-5.{RESET}")

        input(f"\n{YELLOW}Press Enter to continue...{RESET}")
        clear_screen()

if __name__ == "__main__":
    # This ensures the main function is called only when the script is executed directly
    main()
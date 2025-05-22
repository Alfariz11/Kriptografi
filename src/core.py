import os  # For interacting with the operating system (e.g., file paths, creating directories)
import json  # For working with JSON data (serialization and deserialization)
import base64  # For encoding and decoding data in Base64 format
import numpy as np  # For numerical operations, especially for audio data
import soundfile as sf  # For reading and writing audio files
from PIL import Image  # For image processing (currently not used in this snippet but often in steganography)
from PyPDF2 import PdfReader # For reading PDF files and extracting metadata

# Local modules (assumed to be in the same project structure)
from steg import AudioDWT  # For Discrete Wavelet Transform based audio steganography
from crypto import SimplifiedECCCrypto, SimpleRSACrypto  # For ECC and RSA cryptography
from utils import text_to_bits, bits_to_text  # Utility functions for bit manipulation


def image_to_base64(image_path):
    """
    Converts an image file to a Base64 encoded string.

    Args:
        image_path: Path to the image file.

    Returns:
        Base64 encoded string of the image.
    """
    with open(image_path, "rb") as img_file:  # Open image in binary read mode
        return base64.b64encode(img_file.read()).decode('utf-8') # Read, encode, and decode to UTF-8 string


def generate_audio(output_file, duration=10, sample_rate=44100):
    """
    Generates a simple sine wave audio file.

    Args:
        output_file: Path to save the generated audio file.
        duration: Duration of the audio in seconds (default: 10).
        sample_rate: Sample rate of the audio in Hz (default: 44100).

    Returns:
        Path of the generated audio file.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)  # Time array
    audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)  # Generate a 440 Hz sine wave (A4 note)
    sf.write(output_file, audio_data, sample_rate)  # Write audio data to file
    print(f"Sample audio file created: {output_file}")
    return output_file


def prepare_message(message):
    """
    Prepares the message for embedding by performing double encryption (ECC then RSA)
    and creating a header with necessary metadata.

    Args:
        message: The raw message string (text, base64 image, or base64 PDF).

    Returns:
        A tuple containing:
            - all_bits: The combined bit string of header length, header, and encrypted message.
            - ecc_crypto: The ECC cryptography instance used.
            - rsa_crypto: The RSA cryptography instance used.
    """
    # Create ECC instance
    print("Creating ECC keys...")
    ecc_crypto = SimplifiedECCCrypto()
    print("ECC keys created.")

    # Encrypt message with ECC first
    print("Preparing first encryption with ECC...")
    ecc_encrypted_data_base64, ecc_key_base64 = ecc_crypto.encrypt_text(message)

    # Create RSA instance
    print("Creating RSA keys (this might take some time)...")
    rsa_crypto = SimpleRSACrypto()
    print("RSA keys created.")

    # Combine ECC encrypted data and ECC key for RSA encryption
    print("Preparing second encryption with RSA...")
    combined_message = json.dumps({
        "ecc_data": ecc_encrypted_data_base64,
        "ecc_key": ecc_key_base64  # This is the symmetric key used by ECC, encrypted by RSA later
    })

    # Encrypt the combined ECC data with RSA
    rsa_encrypted_data_base64, rsa_key_base64 = rsa_crypto.encrypt_text(combined_message)
    # rsa_key_base64 here is the symmetric key used by RSA for encrypting 'combined_message',
    # which itself needs to be secured. It's included in the header and encrypted with RSA public key.

    # Create header data
    header = {
        "ecc_public_key": ecc_crypto.get_public_key(), # ECC public key for potential direct use by recipient
        "rsa_public_key": rsa_crypto.get_public_key(), # RSA public key of the sender
        "message_length": len(message), # Original message length (before encryption)
        "rsa_key": rsa_key_base64       # The (symmetric) key used for RSA encryption,
                                        # which will be encrypted by recipient's RSA public key or similar mechanism.
                                        # In this SimpleRSACrypto, it might be part of how decryption is keyed.
    }

    # Serialize header and encrypted message to JSON strings
    header_json = json.dumps(header)
    message_json = json.dumps(rsa_encrypted_data_base64) # This is the RSA-encrypted (ECC-encrypted data + ECC key)

    # Convert JSON strings to bit strings
    header_bits = text_to_bits(header_json)
    message_bits = text_to_bits(message_json)

    # Add header length (fixed 32 bits) to know how many bits to read for the header
    header_length_bits = format(len(header_bits), '032b') # '032b' formats as 32-bit binary string

    # Combine all bit strings: header length + header + encrypted message
    all_bits = header_length_bits + header_bits + message_bits

    return all_bits, ecc_crypto, rsa_crypto


def embed_message(input_file=None, output_file=None, message=None, alpha=0.001, is_image=False, is_pdf=False):
    """
    Embeds a text message, image, or PDF into an audio file using DWT and double encryption.

    Args:
        input_file: Path to the original audio file. If None, prompts user or generates a sample.
        output_file: Path to save the stego audio file. If None, prompts user or uses default.
        message: The text message, path to an image file, or path to a PDF file.
        alpha: Alpha parameter for DWT embedding strength (default: 0.001).
        is_image: Boolean flag indicating if the message is an image path.
        is_pdf: Boolean flag indicating if the message is a PDF path.

    Returns:
        Path to the output stego audio file if successful, None otherwise.
    """
    os.makedirs('output', exist_ok=True) # Ensure 'output' directory exists

    # Get input file path if not provided
    if input_file is None:
        input_file = input("Enter path to original audio file (or leave empty to generate a sample): ").strip()
    if not input_file: # If input is empty, generate a sample audio
        input_file = 'output/sample.wav'
        generate_audio(input_file)

    # Get output file path if not provided
    if output_file is None:
        output_file = input("Enter path for output stego file (default: output/stego.wav): ").strip()
    if not output_file: # If input is empty, use default output path
        output_file = 'output/stego.wav'

    # Get message if not provided
    if message is None:
        if is_pdf:
            message = input("Enter path to PDF file: ")
        elif is_image:
            message = input("Enter path to image file: ")
        else:
            message = input("Enter message: ")

    # Process PDF or image message to Base64 string
    if is_pdf:
        print(f"Processing PDF: {message}")
        try:
            message_content = pdf_to_base64(message) # pdf_to_base64 now returns a JSON string
            if not message_content:
                print("Failed to process PDF file.")
                return None
            message = message_content # The message is now a JSON string containing PDF data and metadata
        except Exception as e:
            print(f"Failed to read PDF: {e}")
            return None
    elif is_image:
        print(f"Processing image: {message}")
        try:
            message = image_to_base64(message) # Convert image to base64
        except Exception as e:
            print(f"Failed to read image: {e}")
            return None

    if not message: # Ensure message is not empty
        print("Message cannot be empty.")
        return None

    # Get alpha value if not provided
    if alpha is None:
        alpha_str = input("Enter DWT alpha value (default 0.001): ").strip()
        alpha = 0.001 # Default alpha
        if alpha_str:
            try:
                alpha = float(alpha_str)
            except ValueError:
                print("Invalid alpha value, using default 0.001.")
    print(f"Using alpha = {alpha}")

    try:
        print("Preparing message with double ECC and RSA encryption...")
        all_bits, ecc_crypto, rsa_crypto = prepare_message(message) # Encrypt and prepare bits
        print(f"Encrypted message length: {len(all_bits)} bits")

        # Initialize AudioDWT
        dwt = AudioDWT(wavelet='db2', level=1) # Using Daubechies 2 wavelet

        # Read audio and apply DWT
        audio_data, sample_rate = dwt.read_audio(input_file)
        coeffs = dwt.apply_dwt(audio_data)

        # Check if message fits in the audio
        capacity = len(coeffs[1]) # Capacity is based on the length of detail coefficients (cA)
        if len(all_bits) > capacity:
            print(f"Message too long! Maximum capacity: {capacity} bits, "
                  f"Encrypted message: {len(all_bits)} bits.")
            return None

        # Embed bits into DWT coefficients
        modified_coeffs = dwt.embed_bits_in_coefficients(coeffs, all_bits, alpha=alpha)
        # Reconstruct audio from modified coefficients
        reconstructed_data = dwt.apply_idwt(modified_coeffs)

        # Handle stereo audio: embed in one channel, keep others original
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1: # Check if stereo
            min_len = min(len(reconstructed_data), len(audio_data))
            reconstructed_stereo = np.zeros((min_len, audio_data.shape[1]))
            reconstructed_stereo[:, 0] = reconstructed_data[:min_len] # Embed in first channel
            for ch in range(1, audio_data.shape[1]): # Copy other channels
                reconstructed_stereo[:, ch] = audio_data[:min_len, ch]
            reconstructed_data = reconstructed_stereo

        # Save stego audio
        dwt.save_audio(output_file, reconstructed_data, sample_rate)
        print(f"Message successfully embedded in file: {output_file}")

        # Save keys to a .key file
        key_file = output_file + ".key"
        with open(key_file, 'w') as f:
            f.write("== ECC KEYS ==\n")
            f.write(f"ECC PUBLIC KEY:\n{ecc_crypto.get_public_key()}\n")
            f.write(f"ECC PRIVATE KEY (for sender only):\n{ecc_crypto.get_private_key()}\n") # Sender's private key
            f.write("== RSA KEYS ==\n")
            f.write(f"RSA PUBLIC KEY:\n{rsa_crypto.get_public_key()}\n")
            f.write(f"RSA PRIVATE KEY (for sender only):\n{rsa_crypto.get_private_key()}\n") # Sender's private key

        # Save embedding information to a .info file
        info_file = output_file + ".info"
        info = {
            "bits_length": len(all_bits),       # Total bits embedded
            "ecc_public_key": ecc_crypto.get_public_key(), # For recipient to verify/use
            "ecc_private_key": ecc_crypto.get_private_key(), # Sender's private key (for reference/backup)
            "rsa_public_key": rsa_crypto.get_public_key(),   # For recipient to verify/use
            "rsa_private_key": rsa_crypto.get_private_key(), # Sender's private key (for reference/backup)
            "message_length": len(message),     # Original message length (useful for extraction context)
            "alpha": alpha                      # Alpha value used
        }
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=4) # Save info as JSON

        print(f"Keys saved in: {key_file}")
        print(f"Additional info saved in: {info_file}")
        return output_file

    except Exception as e:
        print(f"Error during message preparation or embedding: {e}")
        # import traceback
        # traceback.print_exc() # For more detailed error logging during development
        return None


def extract_message(stego_file=None):
    """
    Extracts the hidden message from a stego audio file.

    Args:
        stego_file: Path to the stego audio file. If None, prompts user.

    Returns:
        A dictionary containing the extracted message and its type if successful,
        or the raw decrypted message for backward compatibility. None if failed.
        Example dict: {"type": "text" | "image" | "pdf", "message": "...", "path": "..." (for PDF)}
    """
    # Import cryptographic modules locally if not already at top level, or ensure they are accessible
    # from crypto import SimpleRSACrypto, SimplifiedECCCrypto
    # from utils import bits_to_text

    # Get stego file path if not provided
    if stego_file is None:
        stego_file = input("Enter path to stego audio file: ").strip()
    if not stego_file or not os.path.exists(stego_file):
        print("Stego file not found.")
        return None

    # Try to load information from .info file
    info_file = stego_file + ".info"
    ecc_private_key_str = None # String representation of ECC private key
    rsa_private_key_str = None # String representation of RSA private key
    alpha_used = 0.001 # Default alpha if not found in info

    if os.path.exists(info_file):
        try:
            with open(info_file, 'r') as f:
                info = json.load(f)
            num_bits_to_extract = info["bits_length"]
            # These keys are the SENDER's private keys, primarily for sender's reference.
            # For decryption, the RECIPIENT would use their own private keys.
            # However, this simplified crypto might use them differently or assume key exchange happened.
            ecc_private_key_str = info.get("ecc_private_key")
            rsa_private_key_str = info.get("rsa_private_key")
            if "alpha" in info:
                alpha_used = info["alpha"]
            print(f"Using alpha from info file: {alpha_used}")
            print(f"Number of bits to extract from info file: {num_bits_to_extract}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error reading info file ({e}), will ask for number of bits.")
            num_bits_to_extract = int(input("Enter the number of bits for the embedded message: "))
    else:
        print("Info file not found, please enter the number of bits for the embedded message.")
        num_bits_to_extract = int(input("Enter the number of bits for the embedded message: "))

    # Initialize AudioDWT
    dwt = AudioDWT(wavelet='db2', level=1)

    try:
        # Read stego audio and apply DWT
        stego_data, sample_rate = dwt.read_audio(stego_file)
        coeffs = dwt.apply_dwt(stego_data)
        # Extract bits from DWT coefficients
        all_extracted_bits = dwt.extract_bits_from_coefficients(coeffs, num_bits_to_extract, alpha=alpha_used)

        if len(all_extracted_bits) < 32: # Check if enough bits for header length
            print("Extracted data is too short to contain header length!")
            return None

        # Extract header length (first 32 bits)
        header_length_bits = all_extracted_bits[:32]
        try:
            header_length = int(header_length_bits, 2) # Convert binary string to integer
        except ValueError:
            print(f"Invalid header length bits: {header_length_bits}")
            return None

        if len(all_extracted_bits) < 32 + header_length: # Check if enough bits for header
            print("Extracted data is too short to contain the full header!")
            return None

        # Extract header bits and convert to JSON string
        header_bits = all_extracted_bits[32:32 + header_length]
        header_json = bits_to_text(header_bits)

        try:
            header = json.loads(header_json) # Parse header JSON
            # ecc_public_key = header["ecc_public_key"] # Sender's ECC public key
            # rsa_public_key = header["rsa_public_key"] # Sender's RSA public key
            # original_message_length = header["message_length"] # Original message length
            rsa_session_key_base64 = header["rsa_key"] # Symmetric key used by RSA, part of the header
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing header JSON: {e}")
            return None

        # Extract encrypted message bits and convert to JSON string
        encrypted_message_bits = all_extracted_bits[32 + header_length:]
        encrypted_message_json = bits_to_text(encrypted_message_bits)

        try:
            # This is the RSA-encrypted (ECC-encrypted data + ECC key)
            rsa_encrypted_payload_base64 = json.loads(encrypted_message_json)
        except json.JSONDecodeError:
            print("Failed to parse RSA encrypted payload JSON.")
            return None

        # Initialize RSA cryptography for decryption
        rsa_crypto = SimpleRSACrypto()
        if rsa_private_key_str: # If sender's RSA private key is available (e.g., sender is extracting)
            rsa_crypto.load_key(rsa_private_key_str) # This would be recipient's private key in a typical scenario.
                                                    # In SimpleRSACrypto, it might be used to decrypt the session key.

        try:
            # Decrypt RSA layer
            # The rsa_session_key_base64 is the symmetric key used for the payload encryption.
            # How it's handled depends on SimpleRSACrypto. It might need to be decrypted first if it was
            # encrypted with the recipient's public key, or used directly if it's a shared secret.
            combined_message_json = rsa_crypto.decrypt_text(rsa_encrypted_payload_base64, rsa_session_key_base64)
            combined_data = json.loads(combined_message_json) # Parse the JSON containing ECC data and key
            ecc_encrypted_data_base64 = combined_data["ecc_data"]
            ecc_session_key_base64 = combined_data["ecc_key"] # Symmetric key used by ECC

            # Initialize ECC cryptography for decryption
            ecc_crypto = SimplifiedECCCrypto()
            if ecc_private_key_str: # If sender's ECC private key is available
                ecc_crypto.load_key(ecc_private_key_str) # Similar to RSA, recipient would use their private key.

            # Decrypt ECC layer
            decrypted_message = ecc_crypto.decrypt_text(ecc_encrypted_data_base64, ecc_session_key_base64)
            
            print(f"\nExtracted message (first 100 chars):\n{decrypted_message[:100]}"
                  + ("..." if len(decrypted_message) > 100 else ""))

            # Attempt to determine the type of the decrypted message (PDF, image, or plain text)
            try:
                # Try to parse as JSON (this is how PDF data is structured)
                message_data_json = json.loads(decrypted_message)
                if isinstance(message_data_json, dict) and \
                   message_data_json.get("metadata", {}).get("type") == "pdf":
                    # It's a PDF, save it
                    pdf_file_path = save_extracted_pdf(decrypted_message) # Pass the full JSON string
                    if pdf_file_path:
                        print(f"PDF file saved to: {pdf_file_path}")
                    return {"type": "pdf", "message": "PDF content extracted.", "path": pdf_file_path}
                else:
                    # It's some other JSON, return as text for now
                    return {"type": "text", "message": decrypted_message}
            except json.JSONDecodeError:
                # Not JSON, could be Base64 image or plain text
                # Basic check for Base64 (heuristic, not foolproof)
                # A more robust check would involve trying to decode and identify image headers.
                is_likely_base64 = (len(decrypted_message) > 100 and
                                   all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
                                       for c in decrypted_message[:1000].replace("\n", ""))) # Check a larger portion
                if is_likely_base64: # Heuristic for base64 (often images)
                     # Attempt to decode a small part to see if it's valid base64
                    try:
                        base64.b64decode(decrypted_message[:1000].encode('utf-8'))
                        return {"type": "image", "message": decrypted_message} # Return base64 string for image
                    except Exception:
                        # Not valid base64, treat as text
                        return {"type": "text", "message": decrypted_message}
                else:
                    # Likely plain text
                    return {"type": "text", "message": decrypted_message}

            # return decrypted_message # Fallback for very old compatibility if needed

        except Exception as e:
            print(f"Failed during RSA or ECC decryption: {e}")
            # import traceback
            # traceback.print_exc()
            return None

    except Exception as e:
        print(f"Error during extraction: {e}")
        # import traceback
        # traceback.print_exc()
        return None


def debug_extract(stego_file=None, num_bits=None):
    """
    Debug function to extract and print parts of the embedded data
    without full decryption. Helps in diagnosing embedding/extraction issues.
    """
    # Prompt for stego file if not provided
    if stego_file is None:
        stego_file = input("Enter path of the audio file to debug: ").strip()

    if not stego_file or not os.path.exists(stego_file):
        print("File not found.")
        return

    # Get number of bits from .info file or prompt user
    if num_bits is None:
        info_file = stego_file + ".info"
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r') as f:
                    info = json.load(f)
                num_bits = info["bits_length"]
                print(f"Number of bits from info file: {num_bits}")
            except Exception as e:
                print(f"Error reading info file: {str(e)}")
                num_bits = int(input("Enter the number of bits to extract for debugging: "))
        else:
            num_bits = int(input("Enter the number of bits to extract for debugging: "))

    # Initialize DWT
    dwt = AudioDWT(wavelet='db2', level=1)

    try:
        print(f"Extracting {num_bits} bits from the file...")
        stego_data, sample_rate = dwt.read_audio(stego_file)
        coeffs = dwt.apply_dwt(stego_data)

        # Use a default alpha or alpha from info file if available
        alpha_debug = 0.001 # Default for debug; ideally use the one from .info if present
        if 'info' in locals() and 'alpha' in info: # Check if info was loaded and has alpha
            alpha_debug = info['alpha']
            print(f"Using alpha from info for debug: {alpha_debug}")

        all_extracted_bits = dwt.extract_bits_from_coefficients(coeffs, num_bits, alpha=alpha_debug)
        print(f"Number of bits successfully extracted: {len(all_extracted_bits)}")

        if len(all_extracted_bits) < 32:
            print("ERROR: Extracted data is too short! Minimum 32 bits required for header length.")
            return

        # Read header length
        header_length_bits_debug = all_extracted_bits[:32]
        try:
            header_length_debug = int(header_length_bits_debug, 2)
            print(f"Header length: {header_length_debug} bits")
        except ValueError:
            print(f"ERROR: Invalid header length bits: {header_length_bits_debug}")
            return

        # Check data length
        if len(all_extracted_bits) < 32 + header_length_debug:
            print(f"ERROR: Extracted data too short! Need {32 + header_length_debug} bits, only got {len(all_extracted_bits)} bits.")
            return

        # Extract header
        header_bits_debug = all_extracted_bits[32:32 + header_length_debug]
        header_text_debug = bits_to_text(header_bits_debug)

        print("\n===== EXTRACTED HEADER (first 3 lines) =====")
        header_lines_debug = header_text_debug.split('\n')
        for i in range(min(3, len(header_lines_debug))):
            print(header_lines_debug[i])

        try:
            header_debug_json = json.loads(header_text_debug)
            print("\n== HEADER PARSED SUCCESSFULLY ==")
            print(f"Message length from header: {header_debug_json.get('message_length', 'N/A')}")
            if 'ecc_public_key' in header_debug_json:
                print("ECC public key found in header.")
            if 'rsa_public_key' in header_debug_json:
                print("RSA public key found in header.")
            if 'rsa_key' in header_debug_json:
                print("RSA session key found in header.")
        except json.JSONDecodeError as e_json:
            print(f"\nERROR: Failed to parse header JSON: {str(e_json)}")
            print(f"Raw header JSON (first 100 chars): {header_text_debug[:100]}...")

        # Extract message part
        if len(all_extracted_bits) <= 32 + header_length_debug:
            print("ERROR: No message data found after header!")
            return

        message_bits_debug = all_extracted_bits[32 + header_length_debug:]
        message_text_debug = bits_to_text(message_bits_debug)

        print("\n== ENCRYPTED MESSAGE (start) ==")
        print(message_text_debug[:100] + "..." if len(message_text_debug) > 100 else message_text_debug)

        try:
            _ = json.loads(message_text_debug) # Try parsing the encrypted message (it should be a JSON string)
            print("\n== ENCRYPTED MESSAGE PARSED SUCCESSFULLY (as JSON string) ==")
            print("The encrypted message is a valid JSON string.")
        except json.JSONDecodeError as e_msg_json:
            print(f"\nERROR: Failed to parse encrypted message JSON: {str(e_msg_json)}")
            print(f"This means the content extracted for the message part is not a valid JSON string as expected.")

    except Exception as e_debug:
        print(f"DEBUG ERROR: {str(e_debug)}")
        # import traceback
        # traceback.print_exc()


def pdf_to_base64(pdf_path):
    """
    Converts a PDF file to a JSON string containing its Base64 encoded content and metadata.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A JSON string with PDF metadata and Base64 content, or None if an error occurs.
    """
    try:
        # Read PDF file as binary data
        with open(pdf_path, "rb") as pdf_file:
            pdf_binary_content = pdf_file.read()

        # Convert binary data to Base64 string
        pdf_base64_content = base64.b64encode(pdf_binary_content).decode('utf-8')

        # Extract metadata using PyPDF2
        pdf_reader = PdfReader(pdf_path)

        # Create PDF metadata dictionary
        pdf_metadata = {
            "type": "pdf", # Identifier for the content type
            "filename": os.path.basename(pdf_path), # Original filename
            "pages": len(pdf_reader.pages), # Number of pages
            "size": len(pdf_binary_content) # Size in bytes
        }

        # Combine metadata and content into a single dictionary
        result_data = {
            "metadata": pdf_metadata,
            "content": pdf_base64_content
        }

        return json.dumps(result_data) # Return as a JSON string
    except Exception as e:
        print(f"Error reading or processing PDF: {e}")
        return None


def save_extracted_pdf(pdf_json_data_str, output_file_path=None):
    """
    Saves extracted PDF data (from a JSON string) to a file.

    Args:
        pdf_json_data_str: JSON string containing PDF metadata and Base64 content.
        output_file_path: Optional path to save the output PDF file.
                         If None, a default path is generated.

    Returns:
        Path to the saved PDF file if successful, None otherwise.
    """
    try:
        # Parse the JSON string
        pdf_data_dict = json.loads(pdf_json_data_str)

        # Validate that it's PDF data
        if not (isinstance(pdf_data_dict, dict) and
                pdf_data_dict.get("metadata", {}).get("type") == "pdf" and
                "content" in pdf_data_dict):
            print("Extracted data is not a valid PDF structure.")
            return None

        # Get original filename from metadata
        original_filename = pdf_data_dict["metadata"].get("filename", "extracted.pdf")

        # Create output directory if it doesn't exist
        output_dir = 'output/pdf'
        os.makedirs(output_dir, exist_ok=True)

        # Determine output file path
        if not output_file_path:
            output_file_path = os.path.join(output_dir, original_filename)
        
        # Ensure unique filename if it already exists by appending a number
        base, ext = os.path.splitext(output_file_path)
        counter = 1
        temp_output_path = output_file_path
        while os.path.exists(temp_output_path):
            temp_output_path = f"{base}_{counter}{ext}"
            counter += 1
        output_file_path = temp_output_path


        # Decode Base64 content to binary data
        pdf_binary_content = base64.b64decode(pdf_data_dict["content"])

        # Write binary data to the output file
        with open(output_file_path, 'wb') as f:
            f.write(pdf_binary_content)

        print(f"PDF file successfully extracted and saved to: {output_file_path}")
        return output_file_path

    except json.JSONDecodeError:
        print("Invalid JSON format for PDF data.")
        return None
    except KeyError:
        print("Incomplete PDF data (missing 'metadata' or 'content').")
        return None
    except Exception as e:
        print(f"Error saving extracted PDF: {e}")
        return None
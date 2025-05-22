def text_to_bits(text):
    """
    Converts a string of text into a binary string (e.g., "10101100...").
    Each character is converted to its 8-bit ASCII/UTF-8 representation.

    Args:
        text: The input string.

    Returns:
        A string representing the binary data.
    """
    bits = ""
    for char in text:
        # ord(char) gets the integer Unicode code point of the character.
        # format(..., '08b') converts the integer to an 8-bit binary string, zero-padded.
        # Note: For characters outside basic ASCII (code point > 255), this will error
        # if '08b' is strictly enforced for single-byte. A more robust approach for general
        # Unicode text would be to first encode the text to a byte sequence (e.g., UTF-8)
        # and then convert those bytes to bits.
        # However, if text is assumed to be compatible with 8-bit representation per char (e.g. extended ASCII):
        bits += format(ord(char), '08b')
    return bits

def bits_to_text(bits):
    """
    Converts a binary string (e.g., "10101100...") back into a string of text.
    Assumes each 8 bits in the binary string represents one character.

    Args:
        bits: The binary string.

    Returns:
        The decoded text string.
    """
    text = ""
    # Iterate through the bits string in 8-bit chunks.
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits): # Ensure there's a full byte to process
            byte = bits[i:i+8] # Extract an 8-bit chunk.
            # int(byte, 2) converts the binary string byte to an integer.
            # chr(...) converts the integer back to its corresponding character.
            text += chr(int(byte, 2))
    return text

def bytes_to_bits(data):
    """
    Converts a bytes object (sequence of bytes) into a binary string.

    Args:
        data: The input bytes object (e.g., b'\x48\x65').

    Returns:
        A string representing the binary data.
    """
    bits = ""
    for byte_val in data: # Iterate over each byte in the bytes object.
        # byte_val is an integer (0-255).
        # format(byte_val, '08b') converts it to an 8-bit binary string.
        bits += format(byte_val, '08b')
    return bits

def bits_to_bytes(bits):
    """
    Converts a binary string back into a bytes object.
    Assumes the binary string's length is a multiple of 8.

    Args:
        bits: The binary string.

    Returns:
        A bytes object representing the decoded binary data.
    """
    bytes_data = bytearray() # Use bytearray for efficient appending of bytes.
    # Iterate through the bits string in 8-bit chunks.
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits): # Ensure there's a full byte to process.
            byte_str = bits[i:i+8] # Extract an 8-bit chunk.
            # int(byte_str, 2) converts the binary string to an integer.
            # bytearray.append() adds this integer (as a byte) to the array.
            bytes_data.append(int(byte_str, 2))
    return bytes(bytes_data) # Convert the bytearray to an immutable bytes object.
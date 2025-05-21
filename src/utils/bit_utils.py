"""
Utilitas konversi antara teks, bit, dan byte.
"""

def text_to_bits(text):
    """Konversi teks ke string bit."""
    bits = ""
    for char in text:
        bits += format(ord(char), '08b')  # Konversi karakter ke 8 bit
    return bits

def bits_to_text(bits):
    """Konversi string bit kembali ke teks."""
    text = ""
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits):
            byte = bits[i:i+8]
            text += chr(int(byte, 2))
    return text

def bytes_to_bits(data):
    """Konversi bytes ke string bit."""
    bits = ""
    for byte in data:
        bits += format(byte, '08b')
    return bits

def bits_to_bytes(bits):
    """Konversi string bit ke bytes."""
    bytes_data = bytearray()
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits):
            byte = bits[i:i+8]
            bytes_data.append(int(byte, 2))
    return bytes(bytes_data)
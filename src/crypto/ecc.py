import os  # Not directly used in this class but often imported.
import hashlib  # For hashing messages (SHA-256).
import base64  # For encoding binary data into text (Base64).
from Cryptodome.PublicKey import ECC  # For Elliptic Curve Cryptography (key generation, import/export).
from Cryptodome.Random import get_random_bytes  # For generating cryptographically secure random bytes (e.g., for AES keys, IVs).
from Cryptodome.Cipher import AES  # For Advanced Encryption Standard (AES) symmetric encryption.
from Cryptodome.Util.Padding import pad, unpad  # For padding/unpadding data to match AES block size.

class SimplifiedECCCrypto:
    """
    A simplified class for demonstrating ECC-like operations, primarily focusing on key management
    and using AES for bulk encryption.
    
    Note: This class simplifies the ECC aspect. In a real ECC hybrid encryption scheme,
    the session_key for AES would be encrypted using the recipient's ECC public key (e.g., ECIES).
    Here, the session_key is returned in plaintext (Base64 encoded) alongside the ciphertext,
    which is insecure for actual data protection but serves for demonstration or if key exchange
    is handled separately.
    """
    def __init__(self):
        """
        Initializes the ECC crypto object by generating a new ECC key pair.
        """
        self.key = None  # Stores the ECC.EccKey object (private key, public key can be derived).
        self.generate_key() # Generate key pair upon instantiation.

    def generate_key(self):
        """
        Generates a new ECC key pair using the P-256 curve.
        P-256 (also known as secp256r1 or prime256v1) is a common and secure curve.
        
        Returns:
            ECC.EccKey: The generated ECC key object.
        """
        self.key = ECC.generate(curve='P-256')
        return self.key

    def get_public_key(self):
        """
        Exports the public key part of the current ECC key pair in PEM format.
        Generates a new key pair if one doesn't exist.

        Returns:
            str: The public key in PEM format (string).
        """
        if not self.key:
            self.generate_key() # Ensure a key pair exists.
        # .public_key() gets the public component.
        # .export_key(format='PEM') serializes it to the standard PEM format.
        return self.key.public_key().export_key(format='PEM')

    def get_private_key(self):
        """
        Exports the private key of the current ECC key pair in PEM format.
        Generates a new key pair if one doesn't exist.

        Returns:
            str: The private key in PEM format (string).
        """
        if not self.key:
            self.generate_key() # Ensure a key pair exists.
        # .export_key(format='PEM') on the full key object exports the private key.
        return self.key.export_key(format='PEM')

    def encrypt_text(self, plaintext: str):
        """
        Encrypts a plaintext string using AES-CBC with a randomly generated session key.
        The session key itself is NOT encrypted with ECC in this simplified version but returned.

        Args:
            plaintext (str): The text to encrypt.

        Returns:
            tuple: A tuple containing:
                - encrypted_data_base64 (str): The AES-encrypted data (IV + ciphertext), Base64 encoded.
                - session_key_base64 (str): The AES session key, Base64 encoded.
                                            **WARNING: In a real system, this key must be
                                            encrypted with the recipient's public key.**
        """
        # 1. Generate a random 16-byte (128-bit) session key for AES.
        session_key = get_random_bytes(16) # AES-128

        # 2. Create an AES cipher object in CBC (Cipher Block Chaining) mode.
        #    AES.new() generates a random IV automatically if not provided.
        cipher_aes = AES.new(session_key, AES.MODE_CBC)

        # 3. Pad the plaintext to be a multiple of AES block size (16 bytes) and encrypt it.
        #    Plaintext must be bytes, so encode the string (e.g., to UTF-8).
        ciphertext = cipher_aes.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))

        # 4. Prepend the Initialization Vector (IV) to the ciphertext.
        #    The IV is needed for decryption and must be transmitted with the ciphertext.
        #    cipher_aes.iv contains the randomly generated IV.
        encrypted_data_with_iv = cipher_aes.iv + ciphertext

        # 5. Convert the encrypted data (IV + ciphertext) and session key to Base64 strings
        #    for easier transmission or storage as text.
        encrypted_data_base64 = base64.b64encode(encrypted_data_with_iv).decode('utf-8')
        session_key_base64 = base64.b64encode(session_key).decode('utf-8')

        return encrypted_data_base64, session_key_base64

    def load_key(self, key_str: str, is_private: bool = True):
        """
        Loads an ECC key (either private or public) from a PEM formatted string.

        Args:
            key_str (str): The ECC key in PEM format.
            is_private (bool): If True, assumes key_str is a private key.
                               If False, assumes it's a public key.
                               (Note: ECC.import_key infers type, but this flag can guide usage).

        Returns:
            bool: True if the key was loaded successfully, False otherwise.
        """
        try:
            # ECC.import_key can typically infer whether it's a public or private key from the PEM content.
            # The is_private flag might be more for conceptual clarity or if specific handling was intended.
            self.key = ECC.import_key(key_str)
            # To be more explicit, one could check `self.key.has_private()` after import
            # if the distinction is critical for subsequent operations.
            return True
        except Exception as e:
            print(f"Error loading ECC key: {str(e)}")
            return False

    def decrypt_text(self, encrypted_data_base64: str, session_key_base64: str):
        """
        Decrypts AES-CBC encrypted data using the provided session key.

        Args:
            encrypted_data_base64 (str): The Base64 encoded encrypted data (IV + ciphertext).
            session_key_base64 (str): The Base64 encoded AES session key.
                                     **WARNING: This key should have been securely transmitted
                                     (e.g., encrypted with ECC) in a real system.**

        Returns:
            str: The decrypted plaintext string.

        Raises:
            ValueError: If padding is incorrect or decryption fails for other AES-related reasons.
            Exception: For other general decryption failures.
        """
        try:
            # 1. Decode the Base64 encoded encrypted data and session key back to bytes.
            encrypted_data_with_iv = base64.b64decode(encrypted_data_base64)
            session_key = base64.b64decode(session_key_base64)

            # 2. Extract the IV from the beginning of the encrypted data.
            #    AES block size is 16 bytes, so IV is typically 16 bytes for CBC mode.
            iv_length = AES.block_size # Should be 16
            iv = encrypted_data_with_iv[:iv_length]
            ciphertext = encrypted_data_with_iv[iv_length:]

            # 3. Create an AES cipher object for decryption with the session key and IV.
            cipher_aes = AES.new(session_key, AES.MODE_CBC, iv)

            # 4. Decrypt the ciphertext and unpad it.
            try:
                decrypted_padded_plaintext = cipher_aes.decrypt(ciphertext)
                plaintext_bytes = unpad(decrypted_padded_plaintext, AES.block_size)
                return plaintext_bytes.decode('utf-8') # Decode from bytes to string (UTF-8 assumed).
            except ValueError as e: # Catches padding errors and other AES issues
                if "padding is incorrect" in str(e).lower() or "mac check failed" in str(e).lower(): # Common error messages
                    # MAC check failed applies to modes like GCM, EAX, not CBC directly unless a custom MAC is involved.
                    # However, "padding is incorrect" is very common for CBC if key is wrong or data corrupted.
                    print("[DEBUG] ECC/AES Decryption: Padding error or data corruption suspected.")
                    raise ValueError("AES decryption failed: Invalid padding or corrupted data.") from e
                else:
                    print(f"[DEBUG] ECC/AES Decryption: AES error: {str(e)}")
                    raise # Re-raise other AES-related ValueErrors
        except Exception as e: # Catch other errors like Base64 decoding issues
            print(f"[DEBUG] ECC Decryption general failure: {type(e).__name__}: {str(e)}")
            raise # Re-raise the caught exception

    def hash_message(self, message):
        """
        Computes the SHA-256 hash of a message.

        Args:
            message (str or bytes): The message to hash. If string, it's UTF-8 encoded.

        Returns:
            str: The hexadecimal representation of the SHA-256 hash.
        """
        if isinstance(message, str):
            message_bytes = message.encode('utf-8')
        elif isinstance(message, bytes):
            message_bytes = message
        else:
            raise TypeError("Message must be a string or bytes.")
            
        # hashlib.sha256() creates a new SHA-256 hash object.
        # .update() feeds data to the hash (can be called multiple times).
        # .hexdigest() returns the hash as a hexadecimal string.
        hasher = hashlib.sha256()
        hasher.update(message_bytes)
        return hasher.hexdigest()
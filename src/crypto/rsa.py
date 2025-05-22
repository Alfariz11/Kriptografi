import os  # Not directly used in this class but often imported.
import base64  # For encoding binary data into text (Base64).
import hashlib  # For hashing messages (SHA-256).
from Cryptodome.PublicKey import RSA  # For RSA public-key cryptography (key generation, import/export).
from Cryptodome.Cipher import PKCS1_OAEP  # For RSA encryption/decryption scheme (Optimal Asymmetric Encryption Padding).
from Cryptodome.Random import get_random_bytes  # For generating cryptographically secure random bytes.
from Cryptodome.Cipher import AES  # For Advanced Encryption Standard (AES) symmetric encryption.
from Cryptodome.Util.Padding import pad, unpad  # For padding/unpadding data to match AES block size.

class SimpleRSACrypto:
    """
    A class for RSA-based hybrid encryption.
    It uses RSA to encrypt a symmetric session key (for AES), and AES to encrypt the actual data.
    This is a common pattern: RSA for key exchange, AES for bulk data encryption.
    """
    def __init__(self, key_size=2048):
        """
        Initializes the RSA crypto object by generating a new RSA key pair.

        Args:
            key_size (int): The size of the RSA key in bits (e.g., 2048, 3072).
                            Larger keys are more secure but slower.
        """
        self.key_size = key_size
        self.key = None  # Stores the RSA.RsaKey object (private key; public key can be derived).
        self.generate_key() # Generate key pair upon instantiation.

    def generate_key(self):
        """
        Generates a new RSA key pair of the specified `key_size`.

        Returns:
            RSA.RsaKey: The generated RSA key object.
        """
        self.key = RSA.generate(self.key_size)
        return self.key

    def get_public_key(self):
        """
        Exports the public key part of the current RSA key pair in PEM format (UTF-8 decoded string).
        Generates a new key pair if one doesn't exist.

        Returns:
            str: The public key in PEM format.
        """
        if not self.key:
            self.generate_key()
        # self.key.publickey() gets the public component of the key.
        # .export_key() serializes it (default format is PEM for public keys).
        # .decode('utf-8') converts the bytes to a string.
        return self.key.publickey().export_key().decode('utf-8')

    def get_private_key(self):
        """
        Exports the private key of the current RSA key pair in PEM format (UTF-8 decoded string).
        Generates a new key pair if one doesn't exist.

        Returns:
            str: The private key in PEM format.
        """
        if not self.key:
            self.generate_key()
        # .export_key() on the full key object exports the private key (default format PEM).
        return self.key.export_key().decode('utf-8')

    def encrypt_text(self, plaintext: str):
        """
        Encrypts a plaintext string using a hybrid RSA-AES scheme.
        1. A random AES session key is generated.
        2. The AES session key is encrypted using the RSA public key.
        3. The plaintext is encrypted using AES with the session key.

        Args:
            plaintext (str): The text to encrypt.

        Returns:
            tuple: A tuple containing:
                - encrypted_data_base64 (str): The AES-encrypted data (IV + ciphertext), Base64 encoded.
                - encrypted_session_key_base64 (str): The RSA-encrypted AES session key, Base64 encoded.
        """
        # 1. Generate a random 16-byte (128-bit) session key for AES.
        session_key = get_random_bytes(16) # For AES-128

        # 2. Encrypt the AES session key using the RSA public key with PKCS1_OAEP padding.
        #    This is the RSA "key encryption" part of the hybrid scheme.
        cipher_rsa = PKCS1_OAEP.new(self.key.publickey()) # Use the public key for encryption.
        encrypted_session_key = cipher_rsa.encrypt(session_key)

        # 3. Encrypt the plaintext message using AES-CBC with the (unencrypted) session key.
        cipher_aes = AES.new(session_key, AES.MODE_CBC) # A new IV is generated automatically.
        # Pad plaintext to be a multiple of AES block size, then encrypt.
        ciphertext = cipher_aes.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))

        # 4. Prepend the Initialization Vector (IV) to the AES ciphertext.
        encrypted_data_with_iv = cipher_aes.iv + ciphertext

        # 5. Convert the AES-encrypted data and RSA-encrypted session key to Base64 strings.
        encrypted_data_base64 = base64.b64encode(encrypted_data_with_iv).decode('utf-8')
        encrypted_session_key_base64 = base64.b64encode(encrypted_session_key).decode('utf-8')

        return encrypted_data_base64, encrypted_session_key_base64

    def load_key(self, key_str: str, is_private: bool = True):
        """
        Loads an RSA key (either private or public) from a PEM formatted string.

        Args:
            key_str (str): The RSA key in PEM format.
            is_private (bool): If True, assumes key_str is a private key.
                               If False, assumes it's a public key.
                               (Note: RSA.import_key infers type, but this flag can guide usage).

        Returns:
            bool: True if the key was loaded successfully, False otherwise.
        """
        try:
            # RSA.import_key can typically infer whether it's a public or private key from the PEM content.
            self.key = RSA.import_key(key_str)
            # One could check `self.key.has_private()` to confirm after import.
            return True
        except Exception as e:
            print(f"Error loading RSA key: {str(e)}")
            return False

    def decrypt_text(self, encrypted_data_base64: str, encrypted_session_key_base64: str):
        """
        Decrypts data encrypted with the hybrid RSA-AES scheme.
        1. The RSA-encrypted AES session key is decrypted using the RSA private key.
        2. The AES-encrypted data is decrypted using the recovered session key.

        Args:
            encrypted_data_base64 (str): The Base64 encoded AES-encrypted data (IV + ciphertext).
            encrypted_session_key_base64 (str): The Base64 encoded RSA-encrypted AES session key.

        Returns:
            str: The decrypted plaintext string.

        Raises:
            ValueError: If RSA or AES decryption fails (e.g., wrong key, corrupted data, padding error).
            Exception: For other general decryption failures.
        """
        try:
            # 1. Decode Base64 encoded inputs back to bytes.
            encrypted_data_with_iv = base64.b64decode(encrypted_data_base64)
            encrypted_session_key = base64.b64decode(encrypted_session_key_base64)

            # 2. Decrypt the AES session key using the RSA private key.
            #    This requires self.key to be the correct private key.
            cipher_rsa = PKCS1_OAEP.new(self.key) # Uses the private key component for decryption.
            try:
                session_key = cipher_rsa.decrypt(encrypted_session_key)
            except ValueError as e: # Often "Incorrect decryption." if key is wrong or data corrupt.
                if "incorrect decryption" in str(e).lower(): # PyCryptodome's common error message
                    print("[DEBUG] RSA Decryption: Failed to decrypt session key - likely incorrect RSA private key or corrupted key data.")
                    raise ValueError("RSA key decryption failed. Check private key or data integrity.") from e
                else:
                    print(f"[DEBUG] RSA Decryption: Unknown error during session key decryption: {str(e)}")
                    raise # Re-raise other RSA decryption ValueErrors

            # 3. Extract IV and AES ciphertext.
            iv_length = AES.block_size # 16 bytes for AES
            iv = encrypted_data_with_iv[:iv_length]
            ciphertext = encrypted_data_with_iv[iv_length:]

            # 4. Decrypt the main data using AES with the recovered session key and IV.
            cipher_aes = AES.new(session_key, AES.MODE_CBC, iv)
            try:
                decrypted_padded_plaintext = cipher_aes.decrypt(ciphertext)
                plaintext_bytes = unpad(decrypted_padded_plaintext, AES.block_size)
                return plaintext_bytes.decode('utf-8') # Decode from bytes to string.
            except ValueError as e: # Catches padding errors, etc.
                if "padding is incorrect" in str(e).lower():
                    print("[DEBUG] AES Decryption: Invalid padding - data may be corrupted or key incorrect.")
                    raise ValueError("AES decryption failed: Invalid padding or corrupted data.") from e
                else:
                    print(f"[DEBUG] AES Decryption: AES error: {str(e)}")
                    raise # Re-raise other AES-related ValueErrors
        except Exception as e: # Catch other errors like Base64 decoding.
            print(f"[DEBUG] RSA/AES Decryption general failure: {type(e).__name__}: {str(e)}")
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

        hasher = hashlib.sha256()
        hasher.update(message_bytes)
        return hasher.hexdigest()
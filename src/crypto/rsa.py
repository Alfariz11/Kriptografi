"""
Implementasi RSA sederhana untuk enkripsi dan dekripsi pesan
"""
import os
import base64
import hashlib
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad

class SimpleRSACrypto:
    def __init__(self, key_size=2048):
        """
        Inisialisasi RSA sederhana
        
        Args:
            key_size (int): Ukuran kunci dalam bit (default: 2048)
        """
        self.key_size = key_size
        self.key = None
        self.generate_key()
    
    def generate_key(self):
        """
        Menghasilkan pasangan kunci RSA
        """
        self.key = RSA.generate(self.key_size)
        return self.key
    
    def get_public_key(self):
        """
        Mendapatkan kunci publik dalam format yang dapat diserialisasi
        """
        if not self.key:
            self.generate_key()
        return self.key.publickey().export_key().decode('utf-8')
    
    def get_private_key(self):
        """
        Mendapatkan kunci privat dalam format yang dapat diserialisasi
        """
        if not self.key:
            self.generate_key()
        return self.key.export_key().decode('utf-8')
    
    def encrypt_text(self, plaintext):
        """
        Enkripsi teks menggunakan pendekatan hybrid
        (AES untuk pesan, RSA untuk kunci sesi)
        
        Args:
            plaintext (str): Teks yang akan dienkripsi
            
        Returns:
            tuple: (encrypted_data_base64, encrypted_session_key_base64)
        """
        # Buat kunci sesi untuk AES
        session_key = get_random_bytes(16)
        
        # Enkripsi session key dengan RSA
        cipher_rsa = PKCS1_OAEP.new(self.key.publickey())
        encrypted_session_key = cipher_rsa.encrypt(session_key)
        
        # Enkripsi pesan dengan AES
        cipher_aes = AES.new(session_key, AES.MODE_CBC)
        ciphertext = cipher_aes.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        
        # Gabungkan IV dan ciphertext
        encrypted_data = cipher_aes.iv + ciphertext
        
        # Konversi ke base64 untuk kemudahan penanganan
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')
        encrypted_session_key_base64 = base64.b64encode(encrypted_session_key).decode('utf-8')
        
        return encrypted_data_base64, encrypted_session_key_base64
    
    def load_key(self, key_str, is_private=True):
        """
        Memuat kunci RSA dari string PEM.
        
        Args:
            key_str (str): String PEM yang berisi kunci
            is_private (bool): True jika kunci private, False jika kunci public
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            if is_private:
                self.key = RSA.import_key(key_str)
            else:
                self.key = RSA.import_key(key_str)
            return True
        except Exception as e:
            print(f"Error saat memuat kunci: {str(e)}")
            return False
    
    def decrypt_text(self, encrypted_data_base64, encrypted_session_key_base64):
        """
        Dekripsi teks yang dienkripsi
        
        Args:
            encrypted_data_base64 (str): Data terenkripsi dalam format base64
            encrypted_session_key_base64 (str): Kunci sesi terenkripsi dalam format base64
            
        Returns:
            str: Teks yang didekripsi
        """
        try:
            # Dekode dari base64
            encrypted_data = base64.b64decode(encrypted_data_base64)
            encrypted_session_key = base64.b64decode(encrypted_session_key_base64)
            
            # Dekripsi kunci sesi dengan RSA
            cipher_rsa = PKCS1_OAEP.new(self.key)
            try:
                session_key = cipher_rsa.decrypt(encrypted_session_key)
            except ValueError as e:
                if "Incorrect decryption" in str(e):
                    print("[DEBUG] RSA: Dekripsi kunci sesi gagal - kunci tidak cocok")
                    raise ValueError("Kunci RSA tidak cocok untuk dekripsi") from e
                else:
                    print(f"[DEBUG] RSA: Error dekripsi tidak dikenal: {str(e)}")
                    raise
            
            # Pisahkan IV dan ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Dekripsi pesan dengan AES
            cipher_aes = AES.new(session_key, AES.MODE_CBC, iv)
            try:
                plaintext = unpad(cipher_aes.decrypt(ciphertext), AES.block_size)
                return plaintext.decode('utf-8')
            except ValueError as e:
                if "padding is incorrect" in str(e):
                    print("[DEBUG] AES: Padding tidak valid - kemungkinan data rusak")
                    raise ValueError("Padding AES tidak valid, data mungkin rusak") from e
                else:
                    print(f"[DEBUG] AES: Error dekripsi: {str(e)}")
                    raise
        except Exception as e:
            print(f"[DEBUG] Dekripsi gagal: {type(e).__name__}: {str(e)}")
            raise
    
    def hash_message(self, message):
        """
        Menghasilkan hash SHA-256 dari pesan
        
        Args:
            message (str): Pesan yang akan di-hash
            
        Returns:
            str: Hash SHA-256 dalam format hexadecimal
        """
        if isinstance(message, str):
            message = message.encode('utf-8')
        return hashlib.sha256(message).hexdigest() 
"""
Implementasi ECC yang lebih sederhana untuk enkripsi dan dekripsi pesan
Tanpa ketergantungan pada DiffieHellman
"""
import os
import hashlib
import base64
from Cryptodome.PublicKey import ECC
from Cryptodome.Random import get_random_bytes
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad

class SimplifiedECCCrypto:
    def __init__(self):
        """
        Inisialisasi ECC sederhana
        """
        self.key = None
        self.generate_key()
    
    def generate_key(self):
        """
        Menghasilkan pasangan kunci ECC
        """
        self.key = ECC.generate(curve='P-256')
        return self.key
    
    def get_public_key(self):
        """
        Mendapatkan kunci publik dalam format yang dapat diserialisasi
        """
        if not self.key:
            self.generate_key()
        return self.key.public_key().export_key(format='PEM')
    
    def get_private_key(self):
        """
        Mendapatkan kunci privat dalam format yang dapat diserialisasi
        """
        if not self.key:
            self.generate_key()
        return self.key.export_key(format='PEM')
    
    def encrypt_text(self, plaintext):
        # Buat kunci sesi acak untuk AES
        session_key = get_random_bytes(16)
        
        # Enkripsi menggunakan AES
        cipher = AES.new(session_key, AES.MODE_CBC)
        ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        
        # Tambahkan IV ke ciphertext
        encrypted_data = cipher.iv + ciphertext
        
        # Untuk implementasi sederhana, bukannya mengenkripsi session_key dengan ECC,
        # kita hanya akan mengembalikan session_key langsung
        # Di aplikasi nyata, session_key harus dienkripsi dengan kunci publik penerima
        
        # Konversi ke base64 untuk memudahkan penanganan
        encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')
        session_key_base64 = base64.b64encode(session_key).decode('utf-8')
        
        return encrypted_data_base64, session_key_base64
    
    def load_key(self, key_str, is_private=True):
        """
        Memuat kunci ECC dari string PEM.
        
        Args:
            key_str (str): String PEM yang berisi kunci
            is_private (bool): True jika kunci private, False jika kunci public
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            if is_private:
                self.key = ECC.import_key(key_str)
            else:
                self.key = ECC.import_key(key_str)
            return True
        except Exception as e:
            print(f"Error saat memuat kunci ECC: {str(e)}")
            return False
    
    def decrypt_text(self, encrypted_data_base64, session_key_base64):
        try:
            # Dekode dari base64
            encrypted_data = base64.b64decode(encrypted_data_base64)
            session_key = base64.b64decode(session_key_base64)
            
            # Pisahkan IV dan ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Dekripsi menggunakan AES
            try:
                cipher = AES.new(session_key, AES.MODE_CBC, iv)
                plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
                return plaintext.decode('utf-8')
            except ValueError as e:
                if "padding is incorrect" in str(e):
                    print("[DEBUG] ECC/AES: Padding tidak valid - kemungkinan data rusak")
                    raise ValueError("Padding AES tidak valid, data mungkin rusak") from e
                else:
                    print(f"[DEBUG] ECC/AES: Error dekripsi: {str(e)}")
                    raise
        except Exception as e:
            print(f"[DEBUG] ECC Dekripsi gagal: {type(e).__name__}: {str(e)}")
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
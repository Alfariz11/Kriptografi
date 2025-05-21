import numpy as np
import pywt
import soundfile as sf
from scipy import signal

class AudioDWT:
    def __init__(self, wavelet='db1', level=1):
        """
        Inisialisasi AudioDWT dengan tipe wavelet dan level dekomposisi.
        
        Args:
            wavelet (str): Tipe wavelet yang digunakan (default: 'db1')
            level (int): Level dekomposisi DWT (default: 1)
        """
        self.wavelet = wavelet
        self.level = level
    
    def read_audio(self, file_path):
        """
        Membaca file audio dan mengambil data serta sample rate.
        
        Args:
            file_path (str): Path ke file audio
            
        Returns:
            tuple: (data_audio, sample_rate)
        """
        data, sample_rate = sf.read(file_path)
        return data, sample_rate
    
    def save_audio(self, file_path, data, sample_rate):
        """
        Menyimpan data audio ke file.
        
        Args:
            file_path (str): Path untuk menyimpan file audio
            data (numpy.ndarray): Data audio
            sample_rate (int): Sample rate audio
        """
        sf.write(file_path, data, sample_rate)
    
    def apply_dwt(self, audio_data):
        """
        Menerapkan Discrete Wavelet Transform pada data audio.
        
        Args:
            audio_data (numpy.ndarray): Data audio
            
        Returns:
            list: Koefisien wavelet (cA, cD) dimana cA adalah koefisien aproksimasi
                 dan cD adalah koefisien detail
        """
        # Jika data stereo, ambil salah satu channel (misalnya channel pertama)
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            data_for_dwt = audio_data[:, 0]
        else:
            data_for_dwt = audio_data
        
        # Terapkan DWT
        coeffs = pywt.wavedec(data_for_dwt, self.wavelet, level=self.level)
        return coeffs
    
    def apply_idwt(self, coeffs):
        """
        Menerapkan Inverse Discrete Wavelet Transform untuk merekonstruksi data audio.
        
        Args:
            coeffs (list): Koefisien wavelet
            
        Returns:
            numpy.ndarray: Data audio hasil rekonstruksi
        """
        # Rekonstruksi data
        reconstructed_data = pywt.waverec(coeffs, self.wavelet)
        return reconstructed_data
    
    def embed_bits_in_coefficients(self, coeffs, bits, alpha=0.001):
        """
        Menyisipkan bit dalam koefisien detail DWT.
        
        Args:
            coeffs (list): Koefisien wavelet
            bits (str): String bit yang akan disisipkan
            alpha (float): Faktor skala untuk penyisipan (default: 0.001)
            
        Returns:
            list: Koefisien wavelet yang telah dimodifikasi
        """
        # Modifikasi koefisien detail (level 1)
        detail_coeffs = coeffs[1].copy()  # Buat salinan koefisien untuk mencegah modifikasi langsung
        modified_coeffs = list(coeffs.copy())  # Konversi ke list untuk memudahkan manipulasi
        
        # Pastikan ada cukup koefisien untuk menyisipkan seluruh bit
        if len(bits) > len(detail_coeffs):
            raise ValueError(f"Pesan terlalu panjang untuk disisipkan. Maksimal {len(detail_coeffs)} bit")
        
        # Sisipkan bit dalam koefisien detail
        for i in range(len(bits)):
            if i >= len(detail_coeffs):
                break
            
            # Dapatkan nilai absolute dari koefisien
            coeff_abs = abs(detail_coeffs[i])
            
            # Hitung remainder saat ini
            remainder = coeff_abs % (2 * alpha)
            
            # Tentukan target remainder berdasarkan bit
            if bits[i] == '1':
                target_remainder = alpha  # Tepat di tengah range untuk bit 1
            else:
                target_remainder = 0  # Tepat pada 0 untuk bit 0
            
            # Hitung penyesuaian yang diperlukan
            adjustment = target_remainder - remainder
            
            # Terapkan penyesuaian ke koefisien asli
            sign = 1 if detail_coeffs[i] >= 0 else -1
            detail_coeffs[i] = sign * (coeff_abs + adjustment)
        
        # Perbarui koefisien yang telah dimodifikasi
        modified_coeffs[1] = detail_coeffs
        
        return modified_coeffs
    
    def extract_bits_from_coefficients(self, coeffs, num_bits, alpha=0.001):
        """
        Ekstrak bit dari koefisien detail DWT dengan sensitivitas adaptif.
        """
        # Koefisien detail (level 1)
        detail_coeffs = coeffs[1]
        extracted_bits = ""
        
        # Pastikan kita tidak mencoba mengekstrak lebih banyak bit daripada yang tersedia
        max_bits = min(num_bits, len(detail_coeffs))
        
        # Parameter sensitivitas yang adaptif berdasarkan alpha
        threshold_low = 0.4 * alpha
        threshold_high = 1.6 * alpha
        
        # Ekstrak bit dari koefisien detail
        for i in range(max_bits):
            coeff_value = abs(detail_coeffs[i])
            remainder = coeff_value % (2 * alpha)
            
            # Range yang lebih lebar untuk mendeteksi bit 1
            if remainder >= threshold_low and remainder <= threshold_high:
                extracted_bits += "1"
            else:
                extracted_bits += "0"
        
        return extracted_bits
    
    def bits_to_bytes(self, bits):
        """
        Konversi string bit ke bytes.
        
        Args:
            bits (str): String bit
            
        Returns:
            bytes: Data bytes
        """
        # Pastikan panjang bit adalah kelipatan 8
        padded_bits = bits
        if len(bits) % 8 != 0:
            padded_bits = bits + "0" * (8 - (len(bits) % 8))
        
        # Konversi setiap 8 bit ke byte
        bytes_data = bytearray()
        for i in range(0, len(padded_bits), 8):
            byte = padded_bits[i:i+8]
            bytes_data.append(int(byte, 2))
        
        return bytes(bytes_data)
    
    def bytes_to_bits(self, data):
        """
        Konversi bytes ke string bit.
        
        Args:
            data (bytes): Data bytes
            
        Returns:
            str: String bit
        """
        bits = ""
        for byte in data:
            bits += bin(byte)[2:].zfill(8)  # Hilangkan '0b' di awal dan tambahkan 0 hingga 8 bit
        
        return bits
    
    def embed_data(self, audio_path, output_path, data_bits):
        """
        Menyisipkan data bit ke dalam file audio menggunakan DWT.
        
        Args:
            audio_path (str): Path ke file audio asli
            output_path (str): Path untuk menyimpan file audio yang telah disisipi
            data_bits (str): String bit yang akan disisipkan
            
        Returns:
            bool: True jika berhasil
        """
        # Baca file audio
        audio_data, sample_rate = self.read_audio(audio_path)
        
        # Terapkan DWT
        coeffs = self.apply_dwt(audio_data)
        
        # Sisipkan bit
        modified_coeffs = self.embed_bits_in_coefficients(coeffs, data_bits)
        
        # Terapkan IDWT
        reconstructed_data = self.apply_idwt(modified_coeffs)
        
        # Jika audio original stereo, buat hasil rekonstruksi juga stereo
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            # Potong jika ukuran berbeda (seharusnya hampir sama)
            min_len = min(len(reconstructed_data), len(audio_data))
            reconstructed_stereo = np.zeros((min_len, audio_data.shape[1]))
            reconstructed_stereo[:, 0] = reconstructed_data[:min_len]
            # Salin channel lain dari audio asli
            for ch in range(1, audio_data.shape[1]):
                reconstructed_stereo[:, ch] = audio_data[:min_len, ch]
            reconstructed_data = reconstructed_stereo
        
        # Simpan audio hasil
        self.save_audio(output_path, reconstructed_data, sample_rate)
        
        return True
    
    def extract_data(self, stego_audio_path, num_bits):
        """
        Mengekstrak data bit dari file audio yang telah disisipi.
        
        Args:
            stego_audio_path (str): Path ke file audio yang telah disisipi
            num_bits (int): Jumlah bit yang akan diekstrak
            
        Returns:
            str: String bit yang diekstrak
        """
        # Baca file audio stego
        stego_data, sample_rate = self.read_audio(stego_audio_path)
        
        # Terapkan DWT
        coeffs = self.apply_dwt(stego_data)
        
        # Ekstrak bit
        extracted_bits = self.extract_bits_from_coefficients(coeffs, num_bits)
        
        return extracted_bits 
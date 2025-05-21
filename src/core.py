import os
import json
import base64
import numpy as np
import soundfile as sf
from PIL import Image
from PyPDF2 import PdfReader

# Modul lokal
from steg import AudioDWT
from crypto import SimplifiedECCCrypto, SimpleRSACrypto
from utils import text_to_bits, bits_to_text


def image_to_base64(image_path):

    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')
    
def generate_audio(output_file, duration=10, sample_rate=44100):

    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(output_file, audio_data, sample_rate)
    print(f"File audio sampel dibuat: {output_file}")
    return output_file


def prepare_message(message):

    # Buat instance ECC
    print("Membuat kunci ECC...")
    ecc_crypto = SimplifiedECCCrypto()
    print("Kunci ECC dibuat")

    # Enkripsi pesan dengan ECC terlebih dahulu
    print("Menyiapkan enkripsi pertama dengan ECC...")
    ecc_encrypted_data_base64, ecc_key_base64 = ecc_crypto.encrypt_text(message)

    # Buat instance RSA
    print("Membuat kunci RSA (ini mungkin memakan waktu)...")
    rsa_crypto = SimpleRSACrypto()
    print("Kunci RSA dibuat")

    # Enkripsi hasil ECC dengan RSA
    print("Menyiapkan enkripsi kedua dengan RSA...")
    combined_message = json.dumps({
        "ecc_data": ecc_encrypted_data_base64,
        "ecc_key": ecc_key_base64
    })

    rsa_encrypted_data_base64, rsa_key_base64 = rsa_crypto.encrypt_text(combined_message)

    # Buat data header
    header = {
        "ecc_public_key": ecc_crypto.get_public_key(),
        "rsa_public_key": rsa_crypto.get_public_key(),
        "message_length": len(message),
        "rsa_key": rsa_key_base64
    }

    # Serialisasi header dan data terenkripsi
    header_json = json.dumps(header)
    message_json = json.dumps(rsa_encrypted_data_base64)

    # Konversi ke data biner
    header_bits = text_to_bits(header_json)
    message_bits = text_to_bits(message_json)

    # Tambahkan panjang header (32 bit)
    header_length_bits = format(len(header_bits), '032b')

    # Gabungkan semua bit
    all_bits = header_length_bits + header_bits + message_bits

    return all_bits, ecc_crypto, rsa_crypto


def embed_message(input_file=None, output_file=None, message=None, alpha=0.001, is_image=False, is_pdf=False):
    """
    Menyembunyikan pesan, gambar, atau PDF dalam file audio
    
    Args:
        input_file: Path file audio asli (jika None, akan meminta input)
        output_file: Path file audio hasil (jika None, akan meminta input)
        message: Pesan teks, path gambar, atau path PDF 
        alpha: Parameter alpha untuk DWT
        is_image: Flag apakah message adalah path gambar
        is_pdf: Flag apakah message adalah path PDF
        
    Returns:
        Path file output jika berhasil, None jika gagal
    """
    os.makedirs('output', exist_ok=True)

    if input_file is None:
        input_file = input("Masukkan path file audio asli (atau kosong untuk buat sampel): ").strip()
    if not input_file:
        input_file = 'output/sample.wav'
        generate_audio(input_file)

    if output_file is None:
        output_file = input("Masukkan path file output (default: output/stego.wav): ").strip()
    if not output_file:
        output_file = 'output/stego.wav'

    if message is None:
        if is_pdf:
            message = input("Masukkan path PDF: ")
        elif is_image:
            message = input("Masukkan path gambar: ")
        else:
            message = input("Masukkan pesan: ")

    if is_pdf:
        print(f"Memproses PDF: {message}")
        try:
            message = pdf_to_base64(message)
            if not message:
                print("Gagal memproses file PDF")
                return None
        except Exception as e:
            print(f"Gagal membaca PDF: {e}")
            return None
    elif is_image:
        print(f"Memproses gambar: {message}")
        try:
            message = image_to_base64(message)
        except Exception as e:
            print(f"Gagal membaca gambar: {e}")
            return None

    if not message:
        print("Pesan tidak boleh kosong")
        return None

    if alpha is None:
        alpha_str = input("Masukkan nilai alpha DWT (default 0.001): ").strip()
        alpha = 0.001
        if alpha_str:
            try:
                alpha = float(alpha_str)
            except ValueError:
                print("Nilai alpha tidak valid, menggunakan default 0.001")
    print(f"Menggunakan alpha = {alpha}")

    try:
        print("Menyiapkan pesan dengan enkripsi ganda ECC dan RSA...")
        all_bits, ecc_crypto, rsa_crypto = prepare_message(message)
        print(f"Pesan terenkripsi dengan panjang bit: {len(all_bits)} bit")

        dwt = AudioDWT(wavelet='db2', level=1)

        audio_data, sample_rate = dwt.read_audio(input_file)
        coeffs = dwt.apply_dwt(audio_data)

        capacity = len(coeffs[1])
        if len(all_bits) > capacity:
            print(f"Pesan terlalu panjang!, Kapasitas maksimal: {capacity} bit, "
                  f"Pesan terenkripsi: {len(all_bits)} bit")
            return None

        modified_coeffs = dwt.embed_bits_in_coefficients(coeffs, all_bits, alpha=alpha)
        reconstructed_data = dwt.apply_idwt(modified_coeffs)

        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            min_len = min(len(reconstructed_data), len(audio_data))
            reconstructed_stereo = np.zeros((min_len, audio_data.shape[1]))
            reconstructed_stereo[:, 0] = reconstructed_data[:min_len]
            for ch in range(1, audio_data.shape[1]):
                reconstructed_stereo[:, ch] = audio_data[:min_len, ch]
            reconstructed_data = reconstructed_stereo

        dwt.save_audio(output_file, reconstructed_data, sample_rate)
        print(f"Pesan telah berhasil disembunyikan dalam file: {output_file}")

        key_file = output_file + ".key"
        with open(key_file, 'w') as f:
            f.write("== KUNCI ECC ==\n")
            f.write(f"PUBLIC KEY ECC:\n{ecc_crypto.get_public_key()}\n")
            f.write(f"PRIVATE KEY ECC:\n{ecc_crypto.get_private_key()}\n")
            f.write("== KUNCI RSA ==\n")
            f.write(f"PUBLIC KEY RSA:\n{rsa_crypto.get_public_key()}\n")
            f.write(f"PRIVATE KEY RSA:\n{rsa_crypto.get_private_key()}\n")

        info_file = output_file + ".info"
        info = {
            "bits_length": len(all_bits),
            "ecc_public_key": ecc_crypto.get_public_key(),
            "ecc_private_key": ecc_crypto.get_private_key(),
            "rsa_public_key": rsa_crypto.get_public_key(),
            "rsa_private_key": rsa_crypto.get_private_key(),
            "message_length": len(message),
            "alpha": alpha
        }
        with open(info_file, 'w') as f:
            json.dump(info, f)

        print(f"Kunci disimpan di: {key_file}")
        print(f"Informasi tambahan di: {info_file}")
        return output_file

    except Exception as e:
        print(f"Error saat menyiapkan pesan: {e}")
        return None


def extract_message(stego_file=None):
    from crypto import SimpleRSACrypto, SimplifiedECCCrypto
    from utils import bits_to_text

    if stego_file is None:
        stego_file = input("Masukkan path file audio stego: ").strip()
    if not stego_file or not os.path.exists(stego_file):
        print("File tidak ditemukan")
        return None

    info_file = stego_file + ".info"
    ecc_private_key = None
    rsa_private_key = None
    alpha = 0.001

    if os.path.exists(info_file):
        try:
            with open(info_file, 'r') as f:
                info = json.load(f)
            num_bits = info["bits_length"]
            ecc_private_key = info.get("ecc_private_key")
            rsa_private_key = info.get("rsa_private_key")
            if "alpha" in info:
                alpha = info["alpha"]
            print(f"Menggunakan alpha dari file info: {alpha}")
        except json.JSONDecodeError:
            num_bits = int(input("Jumlah bit pesan: "))
    else:
        num_bits = int(input("Jumlah bit pesan: "))

    dwt = AudioDWT(wavelet='db2', level=1)

    try:
        stego_data, sample_rate = dwt.read_audio(stego_file)
        coeffs = dwt.apply_dwt(stego_data)
        all_extracted_bits = dwt.extract_bits_from_coefficients(coeffs, num_bits, alpha=alpha)

        if len(all_extracted_bits) < 32:
            print("Data ekstraksi terlalu pendek!")
            return None

        header_length_bits = all_extracted_bits[:32]
        try:
            header_length = int(header_length_bits, 2)
        except ValueError:
            print(f"Bit header tidak valid: {header_length_bits}")
            return None

        if len(all_extracted_bits) < 32 + header_length:
            print("Header tidak lengkap!")
            return None

        header_bits = all_extracted_bits[32:32 + header_length]
        header_json = bits_to_text(header_bits)

        try:
            header = json.loads(header_json)
            ecc_public_key = header["ecc_public_key"]
            rsa_public_key = header["rsa_public_key"]
            message_length = header["message_length"]
            rsa_key_base64 = header["rsa_key"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing header: {e}")
            return None

        message_bits = all_extracted_bits[32 + header_length:]
        message_json = bits_to_text(message_bits)

        try:
            rsa_encrypted_data_base64 = json.loads(message_json)
        except json.JSONDecodeError:
            print("Gagal parse pesan terenkripsi.")
            return None

        rsa_crypto = SimpleRSACrypto()
        if rsa_private_key:
            rsa_crypto.load_key(rsa_private_key)

        try:
            combined_message = rsa_crypto.decrypt_text(rsa_encrypted_data_base64, rsa_key_base64)
            combined_data = json.loads(combined_message)
            ecc_encrypted_data_base64 = combined_data["ecc_data"]
            ecc_key_base64 = combined_data["ecc_key"]

            ecc_crypto = SimplifiedECCCrypto()
            if ecc_private_key:
                ecc_crypto.load_key(ecc_private_key)

            decrypted_message = ecc_crypto.decrypt_text(ecc_encrypted_data_base64, ecc_key_base64)
            print(f"\nPesan yang diekstrak:\n{decrypted_message[:100]}..." 
                  if len(decrypted_message) > 100 else decrypted_message)
            
            # Deteksi tipe pesan (PDF, gambar, atau teks biasa)
            try:
                # Coba parse sebagai JSON untuk mendeteksi PDF atau format lain
                message_data = json.loads(decrypted_message)
                
                # Jika memiliki metadata dengan tipe PDF, simpan sebagai PDF
                if "metadata" in message_data and message_data["metadata"].get("type") == "pdf":
                    pdf_path = save_extracted_pdf(decrypted_message)
                    if pdf_path:
                        print(f"File PDF disimpan di: {pdf_path}")
                    return {"type": "pdf", "message": decrypted_message, "path": pdf_path}
                else:
                    # JSON lainnya
                    return {"type": "json", "message": decrypted_message}
                    
            except json.JSONDecodeError:
                # Bukan JSON, cek apakah base64 gambar
                if (len(decrypted_message) > 100 and 
                    all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" 
                        for c in decrypted_message[:100])):
                    return {"type": "image", "message": decrypted_message}
                else:
                    # Kemungkinan teks biasa
                    return {"type": "text", "message": decrypted_message}
            
            return decrypted_message  # Compatibility with old code

        except Exception as e:
            print(f"Gagal dekripsi layer RSA: {e}")
            return None

    except Exception as e:
        print(f"Error ekstraksi: {e}")
        return None
    
def debug_extract(stego_file=None, num_bits=None):

    # Tanya nama file audio stego jika tidak diberikan
    if stego_file is None:
        stego_file = input("Masukkan path file audio yang akan di-debug: ").strip()
    
    if not stego_file or not os.path.exists(stego_file):
        print("File tidak ditemukan")
        return
    
    # Cek apakah ada file info untuk mendapatkan jumlah bit
    if num_bits is None:
        info_file = stego_file + ".info"
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r') as f:
                    info = json.load(f)
                num_bits = info["bits_length"]
                print(f"Jumlah bit dari file info: {num_bits}")
            except Exception as e:
                print(f"Error membaca file info: {str(e)}")
                num_bits = int(input("Masukkan jumlah bit yang akan diekstrak untuk debug: "))
        else:
            num_bits = int(input("Masukkan jumlah bit yang akan diekstrak untuk debug: "))
    
    # Buat instance DWT
    dwt = AudioDWT(wavelet='db2', level=1)
    
    try:
        # Ekstrak bit dari file audio
        print(f"Mengekstrak {num_bits} bit dari file...")
        
        # Baca file audio stego
        stego_data, sample_rate = dwt.read_audio(stego_file)
        
        # Terapkan DWT
        coeffs = dwt.apply_dwt(stego_data)
        
        # Ekstrak bit dengan alpha default
        alpha = 0.001  # Nilai alpha default untuk debug
        all_extracted_bits = dwt.extract_bits_from_coefficients(coeffs, num_bits, alpha=alpha)
        
        print(f"Jumlah bit yang berhasil diekstrak: {len(all_extracted_bits)}")
        
        if len(all_extracted_bits) < 32:
            print("ERROR: Data terlalu pendek! Minimal 32 bit diperlukan untuk header.")
            return
        
        # Baca panjang header
        header_length_bits = all_extracted_bits[:32]
        try:
            header_length = int(header_length_bits, 2)
            print(f"Panjang header: {header_length} bit")
        except ValueError:
            print(f"ERROR: Bit header panjang tidak valid: {header_length_bits}")
            return
        
        # Cek panjang data
        if len(all_extracted_bits) < 32 + header_length:
            print(f"ERROR: Data terlalu pendek! Butuh {32 + header_length} bit, hanya ada {len(all_extracted_bits)} bit.")
            return
        
        # Ekstrak header
        header_bits = all_extracted_bits[32:32+header_length]
        header_text = bits_to_text(header_bits)
        
        print("\n===== HEADER TERekstrak (3 baris pertama) =====")
        header_lines = header_text.split('\n')
        for i in range(min(3, len(header_lines))):
            print(header_lines[i])
        
        try:
            header = json.loads(header_text)
            print("\n== HEADER DIPARSE DENGAN SUKSES ==")
            print(f"Message length: {header.get('message_length', 'N/A')}")
            if 'ecc_public_key' in header:
                print("ECC public key tersedia")
            if 'rsa_public_key' in header:
                print("RSA public key tersedia")
            if 'rsa_key' in header:
                print("RSA session key tersedia")
        except json.JSONDecodeError as e:
            print(f"\nERROR: Gagal mem-parse header JSON: {str(e)}")
            print(f"Header JSON raw: {header_text[:100]}...")
        
        # Ekstrak message
        if len(all_extracted_bits) <= 32 + header_length:
            print("ERROR: Tidak ada data pesan!")
            return
        
        message_bits = all_extracted_bits[32+header_length:]
        message_text = bits_to_text(message_bits)
        
        print("\n== PESAN TERENKRIPSI (awal) ==")
        print(message_text[:100] + "..." if len(message_text) > 100 else message_text)
        
        try:
            message_json = json.loads(message_text)
            print("\n== PESAN BERHASIL DIPARSE ==")
            print("Pesan dalam format JSON yang valid")
        except json.JSONDecodeError as e:
            print(f"\nERROR: Gagal mem-parse pesan JSON: {str(e)}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

def pdf_to_base64(pdf_path):
    """Mengkonversi file PDF ke string base64
    
    Args:
        pdf_path: Path ke file PDF
        
    Returns:
        String base64 dari isi PDF dan metadata PDF
    """
    try:
        # Baca file PDF sebagai data biner
        with open(pdf_path, "rb") as pdf_file:
            pdf_binary = pdf_file.read()
        
        # Konversi ke base64
        pdf_base64 = base64.b64encode(pdf_binary).decode('utf-8')
        
        # Ekstrak metadata untuk informasi tambahan
        pdf = PdfReader(pdf_path)
        
        # Buat metadata PDF
        pdf_info = {
            "type": "pdf",
            "filename": os.path.basename(pdf_path),
            "pages": len(pdf.pages),
            "size": len(pdf_binary)
        }
        
        # Gabungkan metadata dan isi
        result = {
            "metadata": pdf_info,
            "content": pdf_base64
        }
        
        return json.dumps(result)
    except Exception as e:
        print(f"Error membaca PDF: {e}")
        return None

def save_extracted_pdf(pdf_json_data, output_file=None):
    """Menyimpan data PDF yang diekstrak ke file
    
    Args:
        pdf_json_data: String JSON dengan metadata dan konten PDF
        output_file: Path file output (opsional)
        
    Returns:
        Path file yang disimpan jika berhasil, None jika gagal
    """
    try:
        # Parse data JSON
        pdf_data = json.loads(pdf_json_data)
        
        # Pastikan ini adalah data PDF
        if pdf_data.get("metadata", {}).get("type") != "pdf":
            print("Data yang diekstrak bukan file PDF")
            return None
        
        # Ambil nama file asli
        original_filename = pdf_data["metadata"]["filename"]
        
        # Buat direktori output jika belum ada
        os.makedirs('output/pdf', exist_ok=True)
        
        # Tentukan path output
        if not output_file:
            output_file = os.path.join('output/pdf', original_filename)
        
        # Decode base64 ke binary data
        pdf_binary = base64.b64decode(pdf_data["content"])
        
        # Tulis ke file
        with open(output_file, 'wb') as f:
            f.write(pdf_binary)
        
        print(f"File PDF berhasil diekstrak dan disimpan di: {output_file}")
        return output_file
    
    except json.JSONDecodeError:
        print("Format JSON tidak valid")
        return None
    except KeyError:
        print("Data PDF tidak lengkap")
        return None
    except Exception as e:
        print(f"Error saat menyimpan PDF: {e}")
        return None
from core import embed_message, extract_message
import time
import os

# ANSI color codes
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def clear_screen():
    """Membersihkan layar terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation(text="Memproses", duration=3):
    """Animasi loading sederhana"""
    for i in range(duration):
        print(f"{YELLOW}{text}{'.' * (i % 3 + 1)}{RESET}", end='\r')
        time.sleep(0.5)
    print(" " * (len(text) + 4), end='\r')  # Clear line

def main():
    clear_screen()
    while True:
        print(f"{BLUE}{'='*60}")
        print("     STEGANOGRAFI AUDIO DENGAN ENKRIPSI ECC, RSA")
        print("                    DAN TRANSFORMASI DWT")
        print("="*60 + RESET)
        print(f"{GREEN}1.{RESET} Sisipkan pesan ke dalam file audio")
        print(f"{GREEN}2.{RESET} Sisipkan gambar ke dalam file audio")
        print(f"{GREEN}3.{RESET} Sisipkan dokumen PDF ke dalam file audio") # Tambahkan opsi PDF
        print(f"{GREEN}4.{RESET} Ekstrak pesan dari file audio")
        print(f"{GREEN}5.{RESET} Keluar")

        choice = input(f"\n{YELLOW}Pilih menu (1-5): {RESET}")

        if choice == '1':
            clear_screen()
            message = input(f"{YELLOW}Masukkan pesan teks: {RESET}")
            loading_animation("Menyembunyikan pesan")
            embed_message(message=message)

        elif choice == '2':
            clear_screen()
            image_path = input(f"{YELLOW}Masukkan path gambar (misal: input/foto.png): {RESET}")
            loading_animation("Memproses gambar")
            try:
                embed_message(message=image_path, is_image=True)
            except Exception as e:
                print(f"{RED}[ERROR] {e}{RESET}")
        
        elif choice == '3': # Tambahkan pilihan untuk PDF
            clear_screen()
            pdf_path = input(f"{YELLOW}Masukkan path dokumen PDF (misal: input/skripsi.pdf): {RESET}")
            loading_animation("Memproses dokumen PDF")
            try:
                embed_message(message=pdf_path, is_pdf=True)
            except Exception as e:
                print(f"{RED}[ERROR] {e}{RESET}")

        elif choice == '4':
            clear_screen()
            print(f"{YELLOW}Ekstraksi pesan dari file audio...{RESET}")
            loading_animation("Mengekstrak data")
            result = extract_message()
            
            if result:
                if isinstance(result, dict):
                    print(f"\n{GREEN}Pesan berhasil diekstrak:{RESET}")
                    
                    if result.get('type') == 'pdf':
                        pdf_path = result.get('path')
                        if pdf_path:
                            print(f"{GREEN}Dokumen PDF berhasil diekstrak dan disimpan di: {pdf_path}{RESET}")
                    elif result.get('type') == 'image':
                        print(f"{GREEN}[Data gambar terdeteksi]{RESET}")
                    else:
                        message = result.get('message', '')
                        print(f"{message[:100] + '...' if len(message) > 100 else message}")
                else:
                    # Backward compatibility
                    print(f"{result[:100] + '...' if len(result) > 100 else result}")
            else:
                print(f"{RED}Gagal mengekstrak pesan atau pesan kosong.{RESET}")

        elif choice == '5':
            print(f"{BLUE}\nKeluar dari program. Terima kasih telah menggunakan aplikasi ini!{RESET}")
            break

        else:
            print(f"{RED}Pilihan tidak valid. Silakan pilih antara 1-5.{RESET}")

        input(f"\n{YELLOW}Tekan Enter untuk melanjutkan...{RESET}")
        clear_screen()

if __name__ == "__main__":
    main()
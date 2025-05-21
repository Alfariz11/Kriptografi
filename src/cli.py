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
        print(f"{GREEN}3.{RESET} Ekstrak pesan dari file audio")
        print(f"{GREEN}4.{RESET} Keluar")

        choice = input(f"\n{YELLOW}Pilih menu (1-4): {RESET}")

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

        elif choice == '3':
            clear_screen()
            print(f"{YELLOW}Ekstraksi pesan dari file audio...{RESET}")
            loading_animation("Mengekstrak data")
            result = extract_message()
            if result:
                print(f"\n{GREEN}Pesan berhasil diekstrak:{RESET}")
                print(f"{result[:100] + '...' if len(result) > 100 else result}")
            else:
                print(f"{RED}Gagal mengekstrak pesan atau pesan kosong.{RESET}")

        elif choice == '4':
            print(f"{BLUE}\nKeluar dari program. Terima kasih telah menggunakan aplikasi ini!{RESET}")
            break

        else:
            print(f"{RED}Pilihan tidak valid. Silakan pilih antara 1-4.{RESET}")

        input(f"\n{YELLOW}Tekan Enter untuk melanjutkan...{RESET}")
        clear_screen()

if __name__ == "__main__":
    main()
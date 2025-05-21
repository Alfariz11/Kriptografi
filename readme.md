# Audio Steganography with ECC, RSA and DWT

This project implements an audio steganography tool that allows users to hide messages or images within audio files using Discrete Wavelet Transform (DWT) and hybrid encryption with ECC and RSA.


## Features

- Hide text messages in audio files
- Hide image files in audio files
- Double-layer encryption using ECC and RSA
- Adjustable DWT parameters for optimal hiding
- Extract hidden messages from stego audio files
- Modern graphical user interface built with PyQt6
- Command line interface also available

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:

```bash
git clone https://github.com/Alfariz11/Kriptografi.git
cd audio-steganography
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Graphical User Interface

To launch the GUI:

```bash
python main.py
```

The GUI provides two main tabs:

1. **Embed Message**: Hide a text message or image inside an audio file
2. **Extract Message**: Extract hidden messages from stego audio files

### Command Line Interface

For batch processing or automation, use the CLI:

```bash
python main.py --cli
```

#### Embed a message:

```bash
python main.py --cli --embed --input INPUT.wav --message "Your secret message" --output OUTPUT.wav
```

#### Embed an image:

```bash
python main.py --cli --embed --input INPUT.wav --image IMAGE.png --output OUTPUT.wav
```

#### Extract a message:

```bash
python main.py --cli --extract --input STEGO.wav
```

## Technical Details

This application uses:

- **Discrete Wavelet Transform (DWT)**: For embedding data in the frequency domain of audio files
- **Elliptic Curve Cryptography (ECC)**: For secure key exchange
- **RSA**: For asymmetric encryption of messages
- **Reed-Solomon Coding**: For error correction
- **PyQt6**: For the graphical user interface

## Project Structure

```

audio-steganography/
│
├── main.py                    # Main entry point
├── requirements.txt           # Dependencies
├── src/
│   ├── core.py                # Core steganography functions
│   ├── gui.py                 # PyQt6 GUI implementation
│   ├── cli.py                 # Command line interface
│   ├── crypto/                # Cryptography modules
│   │   ├── __init__.py
│   │   ├── ecc.py             # ECC implementation
│   │   ├── rsa.py             # RSA implementation
│   │   └── utils.py           # Crypto utilities
│   └── utils/
│       ├── __init__.py
│       ├── audio.py           # Audio processing utilities
│       ├── dwt.py             # DWT implementation
│       └── ecc_coding.py      # Error correction coding
│
└── readme.md                  # Project description
```

## Security Considerations

- The stego files (.wav) must be kept alongside their key files (.wav.key) for successful extraction
- The strength of the encryption relies on keeping the key files secure
- Higher alpha values for DWT embedding make messages more recoverable but may affect audio quality

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- PyWavelets for DWT implementation
- Cryptography library for encryption components
- PyQt6 for the GUI framework

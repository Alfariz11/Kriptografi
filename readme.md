# Audio Steganography with ECC, RSA and DWT

This project implements an audio steganography tool that allows users to hide messages or images within audio files using Discrete Wavelet Transform (DWT) and hybrid encryption with ECC and RSA.

## Features

- Hide text messages in audio files
- Hide image files in audio files
- Double-layer encryption using ECC and RSA
- Adjustable DWT parameters for optimal hiding
- Extract hidden messages from stego audio files
- Modern graphical user interface built with PyQt6
- Advanced quality and security analysis metrics (PSNR, SSIM, MSE, Avalanche Effect)
- Visual report generation with comparative spectrograms
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

The GUI provides three main tabs:

1. **Embed Message**: Hide a text message or image inside an audio file
2. **Extract Message**: Extract hidden messages from stego audio files
3. **Analysis**: Analyze the quality and security metrics of the steganography

### Command Line Interface

For batch processing or automation, use the CLI:

```bash
python main.py --cli
```

#### Embed a message

```bash
python main.py --cli --embed --input INPUT.wav --message "Your secret message" --output OUTPUT.wav
```

#### Embed an image

```bash
python main.py --cli --embed --input INPUT.wav --image IMAGE.png --output OUTPUT.wav
```

#### Extract a message

```bash
python main.py --cli --extract --input STEGO.wav
```

## Analysis Metrics

The application provides several metrics to evaluate the quality and security of the steganography:

### Audio Quality Metrics

- **Mean Square Error (MSE)**: Measures the average squared difference between original and stego audio signals
- **Peak Signal-to-Noise Ratio (PSNR)**: Measures the ratio between the maximum possible power of a signal and the power of corrupting noise
- **Structural Similarity Index (SSIM)**: Measures the similarity between two audio signals based on structural information

### Security Metrics

- **Avalanche Effect**: Measures how a small change in the input message causes significant changes in the encrypted output (ideally close to 50%)

All analysis results can be visualized through automatically generated reports with comparative spectrograms.

## Technical Details

This application uses:

- **Discrete Wavelet Transform (DWT)**: For embedding data in the frequency domain of audio files
- **Elliptic Curve Cryptography (ECC)**: For secure key exchange
- **RSA**: For asymmetric encryption of messages
- **Reed-Solomon Coding**: For error correction
- **PyQt6**: For the graphical user interface
- **Matplotlib & SciPy**: For signal analysis and visualization

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
│   ├── steg/                  # Steganography modules
│   │   ├── __init__.py
│   │   └── dwt.py             # DWT implementation
│   └── utils/
│       ├── __init__.py
│       ├── bit_utils.py       # Bit manipulation utilities
│       └── metrics.py         # Analysis metrics implementation
│
├── output/                    # Output directory
│   ├── audio/                 # Stego audio files
│   ├── image/                 # Extracted images
│   └── reports/               # Analysis reports
│
└── readme.md                  # Project description
```

## Security Considerations

- The stego files (.wav) must be kept alongside their key files (.wav.key) for successful extraction
- The strength of the encryption relies on keeping the key files secure
- Higher alpha values for DWT embedding make messages more recoverable but may affect audio quality
- Analysis metrics can help determine the optimal balance between imperceptibility and robustness

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- PyWavelets for DWT implementation
- Cryptography library for encryption components
- PyQt6 for the GUI framework
- Matplotlib and SciPy for signal analysis and visualization
- scikit-image for structural similarity calculations

```

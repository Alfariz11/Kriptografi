# src/utils/metrics.py
import numpy as np
import soundfile as sf
from scipy import signal
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim
import hashlib
import os

def calculate_mse(original_signal, stego_signal):
    """
    Calculate Mean Square Error (MSE) between original and stego audio signals
    
    Args:
        original_signal: The original audio signal
        stego_signal: The steganography audio signal
    
    Returns:
        The MSE value
    """
    # Ensure signals are the same length for comparison
    min_length = min(len(original_signal), len(stego_signal))
    original = original_signal[:min_length]
    stego = stego_signal[:min_length]
    
    # Handle multi-channel audio by averaging if needed
    if len(original.shape) > 1:
        original = np.mean(original, axis=1)
    if len(stego.shape) > 1:
        stego = np.mean(stego, axis=1)
        
    # Calculate MSE
    mse = np.mean((original - stego) ** 2)
    return mse

def calculate_psnr(original_signal, stego_signal):
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR) between original and stego audio signals
    
    Args:
        original_signal: The original audio signal
        stego_signal: The steganography audio signal
    
    Returns:
        The PSNR value in dB
    """
    mse = calculate_mse(original_signal, stego_signal)
    if mse == 0:  # Same signals
        return float('inf')
    
    # Calculate max possible value (assuming float in range [-1, 1])
    max_possible = 1.0
    
    # Calculate PSNR
    psnr = 10 * np.log10((max_possible ** 2) / mse)
    return psnr

def calculate_ssim(original_signal, stego_signal):
    """
    Calculate Structural Similarity Index (SSIM) between original and stego audio signals
    
    Args:
        original_signal: The original audio signal
        stego_signal: The steganography audio signal
    
    Returns:
        The SSIM value (between -1 and 1, higher is better)
    """
    # Ensure signals are the same length for comparison
    min_length = min(len(original_signal), len(stego_signal))
    original = original_signal[:min_length]
    stego = stego_signal[:min_length]
    
    # Handle multi-channel audio by averaging if needed
    if len(original.shape) > 1:
        original = np.mean(original, axis=1)
    if len(stego.shape) > 1:
        stego = np.mean(stego, axis=1)
    
    # Calculate SSIM
    # For audio, we often need to set the data_range appropriately
    data_range = max(np.max(original) - np.min(original), 
                     np.max(stego) - np.min(stego))
    
    ssim_value = ssim(original, stego, data_range=data_range)
    return ssim_value

def calculate_avalanche_effect(message1, message2=None):
    """
    Calculate the Avalanche Effect to measure the diffusion property of encryption
    
    The Avalanche Effect measures how much the encrypted output changes when 
    the input is slightly modified. For good cryptographic algorithms, a small
    change in input should cause a significant change in the output (close to 50%).
    
    Args:
        message1: First message to encrypt
        message2: Second message with minimal difference (if None, a one-bit different message is created)
    
    Returns:
        The avalanche effect percentage
    """
    if message2 is None:
        # Create a second message with one bit difference
        if isinstance(message1, str):
            # For text messages, change one character
            if not message1:
                return 0
            pos = len(message1) // 2
            char_code = ord(message1[pos])
            # Flip one bit in the character
            new_char = chr(char_code ^ 1)  # XOR with 1 to flip least significant bit
            message2 = message1[:pos] + new_char + message1[pos+1:]
        else:
            # For binary data, flip one bit
            message2 = bytearray(message1)
            if len(message2) > 0:
                pos = len(message2) // 2
                message2[pos] ^= 1  # Flip one bit
    
    # Get hash of both messages (simulating encryption output)
    hash1 = hashlib.sha256(message1.encode() if isinstance(message1, str) else message1).digest()
    hash2 = hashlib.sha256(message2.encode() if isinstance(message2, str) else message2).digest()
    
    # Convert to binary and count differing bits
    bin1 = ''.join(format(byte, '08b') for byte in hash1)
    bin2 = ''.join(format(byte, '08b') for byte in hash2)
    
    # Count differing bits
    diff_bits = sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
    
    # Calculate avalanche effect percentage
    avalanche_effect = (diff_bits / len(bin1)) * 100
    
    return avalanche_effect

def generate_quality_report(original_file, stego_file, output_dir='output/reports'):
    """
    Generate a comprehensive quality report comparing original and stego audio
    
    Args:
        original_file: Path to the original audio file
        stego_file: Path to the stego audio file
        output_dir: Directory to save the report
        
    Returns:
        Dictionary with quality metrics and path to the report file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load audio files
    original_data, original_rate = sf.read(original_file)
    stego_data, stego_rate = sf.read(stego_file)
    
    # Calculate metrics
    mse_value = calculate_mse(original_data, stego_data)
    psnr_value = calculate_psnr(original_data, stego_data)
    ssim_value = calculate_ssim(original_data, stego_data)
    
    # Generate spectrogram comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Original spectrogram
    f, t, Sxx = signal.spectrogram(np.mean(original_data, axis=1) if len(original_data.shape) > 1 else original_data, 
                                  original_rate)
    ax1.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')
    ax1.set_title('Original Audio Spectrogram')
    ax1.set_ylabel('Frequency [Hz]')
    ax1.set_xlabel('Time [sec]')
    
    # Stego spectrogram
    f, t, Sxx = signal.spectrogram(np.mean(stego_data, axis=1) if len(stego_data.shape) > 1 else stego_data, 
                                  stego_rate)
    im = ax2.pcolormesh(t, f, 10 * np.log10(Sxx), shading='gouraud')
    ax2.set_title('Stego Audio Spectrogram')
    ax2.set_ylabel('Frequency [Hz]')
    ax2.set_xlabel('Time [sec]')
    
    # Add colorbar
    plt.colorbar(im, ax=[ax1, ax2], label='Power/Frequency (dB/Hz)')
    
    # Add metrics to the figure
    plt.figtext(0.5, 0.01, f'MSE: {mse_value:.6f} | PSNR: {psnr_value:.2f} dB | SSIM: {ssim_value:.6f}', 
                ha='center', fontsize=12, bbox={'facecolor': 'white', 'alpha': 0.8, 'pad': 5})
    
    # Save the figure
    report_file = os.path.join(output_dir, os.path.basename(stego_file).replace('.wav', '_quality_report.png'))
    plt.tight_layout()
    plt.savefig(report_file)
    plt.close()
    
    # Return metrics
    metrics = {
        'mse': mse_value,
        'psnr': psnr_value,
        'ssim': ssim_value,
        'report_file': report_file
    }
    
    return metrics

def analyze_security(message, output_dir='output/reports'):
    """
    Analyze security aspects of the steganography system
    
    Args:
        message: The message to analyze
        output_dir: Directory to save the report
        
    Returns:
        Dictionary with security metrics
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate avalanche effect
    avalanche_effect_value = calculate_avalanche_effect(message)
    
    # Create slightly different messages to test avalanche effect stability
    avalanche_values = []
    for i in range(10):
        if isinstance(message, str) and len(message) > i:
            # Modify different positions for text
            pos = i % len(message)
            char_code = ord(message[pos])
            new_char = chr(char_code ^ 1)
            modified_message = message[:pos] + new_char + message[pos+1:]
            avalanche_values.append(calculate_avalanche_effect(message, modified_message))
    
    # Calculate average and standard deviation
    avg_avalanche = np.mean(avalanche_values) if avalanche_values else avalanche_effect_value
    std_avalanche = np.std(avalanche_values) if avalanche_values else 0
    
    # Generate avalanche effect plot if we have multiple values
    if avalanche_values:
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(avalanche_values)), avalanche_values)
        plt.axhline(y=50, color='r', linestyle='-', label='Ideal (50%)')
        plt.axhline(y=avg_avalanche, color='g', linestyle='--', label=f'Average ({avg_avalanche:.2f}%)')
        plt.xlabel('Test Case')
        plt.ylabel('Avalanche Effect (%)')
        plt.title('Avalanche Effect Analysis')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        report_file = os.path.join(output_dir, 'avalanche_effect_analysis.png')
        plt.tight_layout()
        plt.savefig(report_file)
        plt.close()
    else:
        report_file = None
    
    # Return security metrics
    security_metrics = {
        'avalanche_effect': avalanche_effect_value,
        'avg_avalanche': avg_avalanche,
        'std_avalanche': std_avalanche,
        'report_file': report_file
    }
    
    return security_metrics

if __name__ == "__main__":
    # Example usage
    print("This module provides audio quality metrics for steganography")
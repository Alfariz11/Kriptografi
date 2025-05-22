# src/utils/metrics.py
import numpy as np  # For numerical operations, especially array manipulation
import soundfile as sf  # For reading and writing audio files
from scipy import signal # For signal processing, like generating spectrograms
import matplotlib.pyplot as plt # For plotting graphs and spectrograms
from skimage.metrics import structural_similarity as ssim # For calculating SSIM (image metric, adapted for 1D audio)
import hashlib # For hashing, used in avalanche effect calculation
import os # For interacting with the operating system, like creating directories and file paths

def calculate_mse(original_signal, stego_signal):
    """
    Calculate Mean Square Error (MSE) between original and stego audio signals.
    MSE measures the average squared difference between the signals. Lower is better.

    Args:
        original_signal: The original audio signal (numpy array).
        stego_signal: The steganography (modified) audio signal (numpy array).

    Returns:
        The MSE value (float).
    """
    # Ensure signals are the same length for comparison by truncating the longer one
    min_length = min(len(original_signal), len(stego_signal))
    original = original_signal[:min_length]
    stego = stego_signal[:min_length]

    # Handle multi-channel audio by averaging across channels to get a 1D signal for comparison
    # This is a simplification; channel-wise MSE could also be considered.
    if original.ndim > 1: # Check if original_signal has more than one dimension (i.e., multi-channel)
        original = np.mean(original, axis=1) # Average along the channel axis (axis=1)
    if stego.ndim > 1: # Check for stego_signal as well
        stego = np.mean(stego, axis=1)

    # Calculate MSE: mean of (original - stego)^2
    mse = np.mean((original - stego) ** 2)
    return mse

def calculate_psnr(original_signal, stego_signal):
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR) between original and stego audio signals.
    PSNR is a measure of the quality of a reconstructed signal. Higher is better.

    Args:
        original_signal: The original audio signal.
        stego_signal: The steganography audio signal.

    Returns:
        The PSNR value in dB (float).
    """
    mse = calculate_mse(original_signal, stego_signal)
    if mse == 0:  # If MSE is 0, signals are identical, PSNR is infinite
        return float('inf')

    # Determine the maximum possible pixel value (or signal amplitude).
    # For audio signals normalized to [-1, 1], MAX_I is 1.
    # If audio is, e.g., 16-bit PCM, MAX_I would be 2^15 - 1 or similar.
    # Assuming signal is float and normalized, so max peak is 1.0 (or data driven max)
    # max_possible = np.max(np.abs(original_signal)) # Alternative: data-driven max
    max_possible = 1.0 # Assuming audio data is normalized to [-1.0, 1.0] or [0, 1.0] peak

    # Calculate PSNR using the formula: 10 * log10(MAX_I^2 / MSE)
    psnr = 10 * np.log10((max_possible ** 2) / mse)
    return psnr

def calculate_ssim(original_signal, stego_signal):
    """
    Calculate Structural Similarity Index (SSIM) between original and stego audio signals.
    SSIM measures the similarity between two signals based on luminance, contrast, and structure.
    Value ranges from -1 to 1, where 1 indicates perfect similarity.

    Args:
        original_signal: The original audio signal.
        stego_signal: The steganography audio signal.

    Returns:
        The SSIM value (float).
    """
    # Ensure signals are the same length
    min_length = min(len(original_signal), len(stego_signal))
    original = original_signal[:min_length]
    stego = stego_signal[:min_length]

    # Handle multi-channel audio by averaging (similar to MSE/PSNR)
    if original.ndim > 1:
        original = np.mean(original, axis=1)
    if stego.ndim > 1:
        stego = np.mean(stego, axis=1)

    # Calculate SSIM. The `data_range` parameter is important.
    # It should be the dynamic range of the data (max_value - min_value).
    data_range_original = np.max(original) - np.min(original)
    data_range_stego = np.max(stego) - np.min(stego)
    data_range = max(data_range_original, data_range_stego)
    if data_range == 0: # Avoid division by zero if signals are flat
        return 1.0 if np.array_equal(original, stego) else 0.0


    # SSIM is typically used for images. For 1D signals like audio,
    # it might require specific windowing or adaptation.
    # The skimage.metrics.structural_similarity can take 1D arrays.
    # win_size might need to be adjusted for audio; if None, it's set based on data length.
    # Ensure win_size is odd and less than signal length.
    # Default win_size is 7 for skimage if not specified and if data allows.
    # For very short signals, this might fail.
    # A common win_size for audio might be larger, e.g., 1024, 2048, but SSIM default is small.
    # Let's use skimage's default behavior or specify a small, safe window if needed.
    win_size = min(7, len(original) - (1 if len(original) % 2 == 0 else 0) ) # ensure win_size is odd and <= len
    if win_size < 3: # SSIM requires win_size >= 3 for some internal calculations
        # If signal too short for default window, might return low similarity or handle as identical
        return 1.0 if np.array_equal(original, stego) else 0.0


    ssim_value = ssim(original, stego, data_range=data_range, win_size=win_size) # Removed multichannel=False as we average first
    return ssim_value

def calculate_avalanche_effect(message1, message2=None):
    """
    Calculate the Avalanche Effect to measure the diffusion property of an encryption-like process (using hashing as a proxy).
    The Avalanche Effect measures how much the output (e.g., hash) changes when
    the input is slightly modified (e.g., one bit flipped).
    A good cryptographic function should ideally have an avalanche effect close to 50%.

    Args:
        message1: First message (string or bytes).
        message2: Second message with a minimal difference (string or bytes).
                  If None, a one-bit different message is created from message1.

    Returns:
        The avalanche effect percentage (float).
    """
    if message2 is None:
        # Create a second message with a one-bit difference from message1
        if isinstance(message1, str):
            if not message1: return 0.0 # Handle empty string
            # For text, convert to bytes, flip a bit, then convert back if needed, or work with bytes.
            # Simpler: change one character slightly.
            msg1_bytes = message1.encode('utf-8')
            temp_bytes = bytearray(msg1_bytes)
            if not temp_bytes: return 0.0
            pos_to_flip = len(temp_bytes) // 2
            temp_bytes[pos_to_flip] ^= 1  # Flip one bit in the byte array
            # For this test, we keep message2 as bytes if message1 was converted
            message2 = bytes(temp_bytes)

        elif isinstance(message1, bytes):
            if not message1: return 0.0
            message2_bytearray = bytearray(message1)
            pos_to_flip = len(message2_bytearray) // 2
            message2_bytearray[pos_to_flip] ^= 1  # Flip one bit
            message2 = bytes(message2_bytearray)
        else:
            raise TypeError("message1 must be string or bytes.")

    # Ensure both messages are bytes for hashing
    msg1_bytes_final = message1.encode('utf-8') if isinstance(message1, str) else message1
    msg2_bytes_final = message2.encode('utf-8') if isinstance(message2, str) else message2

    # Get SHA-256 hash of both messages
    hash1 = hashlib.sha256(msg1_bytes_final).digest() # .digest() returns bytes
    hash2 = hashlib.sha256(msg2_bytes_final).digest()

    # Convert hashes to binary strings to compare bits
    bin1 = ''.join(format(byte, '08b') for byte in hash1) # '08b' for 8-bit binary representation
    bin2 = ''.join(format(byte, '08b') for byte in hash2)

    # Count differing bits
    diff_bits = sum(b1_bit != b2_bit for b1_bit, b2_bit in zip(bin1, bin2))

    # Calculate avalanche effect percentage
    total_bits = len(bin1) # Total bits in the hash output
    if total_bits == 0: return 0.0
    avalanche_percentage = (diff_bits / total_bits) * 100

    return avalanche_percentage

def generate_quality_report(original_file, stego_file, output_dir='output/reports'):
    """
    Generates a comprehensive quality report comparing original and stego audio files.
    The report includes MSE, PSNR, SSIM metrics and a side-by-side spectrogram.

    Args:
        original_file: Path to the original audio file.
        stego_file: Path to the stego audio file.
        output_dir: Directory to save the report image (default: 'output/reports').

    Returns:
        A dictionary containing the calculated quality metrics and the path to the saved report file.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load audio files
    try:
        original_data, original_rate = sf.read(original_file)
        stego_data, stego_rate = sf.read(stego_file)
    except Exception as e:
        print(f"Error loading audio files: {e}")
        return {
            'mse': float('nan'), 'psnr': float('nan'), 'ssim': float('nan'),
            'report_file': None, 'error': str(e)
        }

    if original_rate != stego_rate:
        print("Warning: Sample rates of original and stego files differ. Metrics might be misleading.")
        # Optionally, resample one to match the other, or raise an error

    # Calculate quality metrics
    mse_value = calculate_mse(original_data, stego_data)
    psnr_value = calculate_psnr(original_data, stego_data)
    ssim_value = calculate_ssim(original_data, stego_data)

    # --- Generate spectrogram comparison plot ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6)) # 1 row, 2 columns for side-by-side
    fig.suptitle('Audio Quality Analysis: Original vs. Stego', fontsize=16)

    # Prepare original signal for spectrogram (use mean if stereo)
    original_spec_data = np.mean(original_data, axis=1) if original_data.ndim > 1 else original_data
    f_orig, t_orig, Sxx_orig = signal.spectrogram(original_spec_data, original_rate)
    # Plot original spectrogram with log scale for power
    mesh1 = ax1.pcolormesh(t_orig, f_orig, 10 * np.log10(Sxx_orig + 1e-9), shading='gouraud', cmap='viridis') # add 1e-9 to avoid log(0)
    ax1.set_title('Original Audio Spectrogram')
    ax1.set_ylabel('Frequency [Hz]')
    ax1.set_xlabel('Time [sec]')
    fig.colorbar(mesh1, ax=ax1, format='%+2.0f dB', label='Power/Frequency (dB/Hz)')


    # Prepare stego signal for spectrogram
    stego_spec_data = np.mean(stego_data, axis=1) if stego_data.ndim > 1 else stego_data
    f_steg, t_steg, Sxx_steg = signal.spectrogram(stego_spec_data, stego_rate)
    # Plot stego spectrogram
    mesh2 = ax2.pcolormesh(t_steg, f_steg, 10 * np.log10(Sxx_steg + 1e-9), shading='gouraud', cmap='viridis')
    ax2.set_title('Stego Audio Spectrogram')
    ax2.set_ylabel('Frequency [Hz]') # Keep for clarity, or share y-axis if scales are identical
    ax2.set_xlabel('Time [sec]')
    fig.colorbar(mesh2, ax=ax2, format='%+2.0f dB', label='Power/Frequency (dB/Hz)')


    # Add metrics text to the figure
    metrics_text = f'MSE: {mse_value:.6f}  |  PSNR: {psnr_value:.2f} dB  |  SSIM: {ssim_value:.6f}'
    plt.figtext(0.5, 0.02, metrics_text, ha='center', fontsize=12,
                bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 5})

    # Save the figure
    base_stego_name = os.path.basename(stego_file)
    report_filename = os.path.splitext(base_stego_name)[0] + '_quality_report.png'
    report_file_path = os.path.join(output_dir, report_filename)

    plt.tight_layout(rect=[0, 0.05, 1, 0.95]) # Adjust layout to make space for suptitle and figtext
    plt.savefig(report_file_path)
    plt.close(fig) # Close the figure to free memory

    # Return calculated metrics and report path
    metrics_results = {
        'mse': mse_value,
        'psnr': psnr_value,
        'ssim': ssim_value,
        'report_file': report_file_path
    }
    return metrics_results

def analyze_security(message, output_dir='output/reports'):
    """
    Analyzes security aspects, primarily focusing on the avalanche effect of a hash function
    (as a proxy for encryption quality).

    Args:
        message: The message (string or bytes) to analyze.
        output_dir: Directory to save the analysis report image (default: 'output/reports').

    Returns:
        A dictionary containing security metrics and path to the report file (if generated).
    """
    os.makedirs(output_dir, exist_ok=True) # Ensure output directory exists

    # Calculate a single avalanche effect value for the given message
    avalanche_effect_value = calculate_avalanche_effect(message)

    # Create multiple slightly different messages to test avalanche effect stability and average
    avalanche_values_list = []
    num_tests = 20 # Number of different modified messages to test
    msg_bytes_for_tests = message.encode('utf-8') if isinstance(message, str) else message

    if len(msg_bytes_for_tests) > 0:
        for i in range(num_tests):
            # Modify a different bit for each test case, cycling through the message if shorter than num_tests
            modified_msg_bytes = bytearray(msg_bytes_for_tests)
            bit_to_flip_in_byte = i % 8
            byte_to_flip_in_msg = (i // 8) % len(modified_msg_bytes)

            modified_msg_bytes[byte_to_flip_in_msg] ^= (1 << bit_to_flip_in_byte) # Flip the i-th bit overall

            avalanche_values_list.append(calculate_avalanche_effect(msg_bytes_for_tests, bytes(modified_msg_bytes)))
    else: # Handle empty message
        avalanche_values_list.append(0.0)


    # Calculate average and standard deviation of avalanche effects
    avg_avalanche = np.mean(avalanche_values_list) if avalanche_values_list else avalanche_effect_value
    std_avalanche = np.std(avalanche_values_list) if avalanche_values_list else 0.0

    # Generate avalanche effect plot if multiple values were calculated
    report_file_path_security = None
    if avalanche_values_list:
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(avalanche_values_list)), avalanche_values_list, color='skyblue', label='Individual Tests')
        plt.axhline(y=50, color='red', linestyle='-', linewidth=2, label='Ideal (50%)')
        plt.axhline(y=avg_avalanche, color='green', linestyle='--', linewidth=2, label=f'Average ({avg_avalanche:.2f}%)')

        plt.xlabel('Test Case (Different Single Bit Flipped in Input)')
        plt.ylabel('Avalanche Effect (%)')
        plt.title('Avalanche Effect Analysis (SHA-256 Proxy)')
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.ylim(0, 100) # Avalanche effect is a percentage

        report_filename_security = 'avalanche_effect_analysis.png'
        report_file_path_security = os.path.join(output_dir, report_filename_security)
        plt.tight_layout()
        plt.savefig(report_file_path_security)
        plt.close() # Close the figure

    # Return security metrics
    security_metrics_results = {
        'avalanche_effect': avalanche_effect_value, # Single test on original message
        'avg_avalanche': avg_avalanche,        # Average over multiple tests
        'std_avalanche': std_avalanche,        # Standard deviation over multiple tests
        'report_file': report_file_path_security # Path to the plot
    }
    return security_metrics_results

if __name__ == "__main__":
    # This block is executed when the script is run directly.
    # Useful for testing the functions in this module.
    print("This module provides audio quality and security (avalanche effect) metrics.")
    print("Example usage would involve calling these functions with appropriate audio files or messages.")

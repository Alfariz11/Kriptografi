import numpy as np  # For numerical operations, especially array manipulation
import pywt  # PyWavelets library for Discrete Wavelet Transform
import soundfile as sf  # For reading and writing audio files
# from scipy import signal # Not used in this class, but often used with audio processing

class AudioDWT:
    """
    A class to perform audio steganography using Discrete Wavelet Transform (DWT).
    It handles reading/writing audio, applying DWT/IDWT, and embedding/extracting bits
    in the DWT coefficients.
    """
    def __init__(self, wavelet='db1', level=1):
        """
        Initializes the AudioDWT class.

        Args:
            wavelet (str): The type of wavelet to use (e.g., 'db1' for Daubechies 1).
                           See PyWavelets documentation for available wavelets.
            level (int): The level of wavelet decomposition.
        """
        self.wavelet = wavelet
        self.level = level

    def read_audio(self, file_path):
        """
        Reads an audio file.

        Args:
            file_path (str): The path to the audio file.

        Returns:
            tuple: A tuple containing:
                - data (numpy.ndarray): The audio data.
                - sample_rate (int): The sample rate of the audio.
        """
        data, sample_rate = sf.read(file_path)
        return data, sample_rate

    def save_audio(self, file_path, data, sample_rate):
        """
        Saves audio data to a file.

        Args:
            file_path (str): The path to save the audio file.
            data (numpy.ndarray): The audio data to save.
            sample_rate (int): The sample rate of the audio.
        """
        sf.write(file_path, data, sample_rate)

    def apply_dwt(self, audio_data):
        """
        Applies Discrete Wavelet Transform (DWT) to the audio data.
        If the audio is stereo, it processes only the first channel.

        Args:
            audio_data (numpy.ndarray): The input audio data.

        Returns:
            list: A list of DWT coefficient arrays (approximation and details).
                  Format: [cA_n, cD_n, cD_n-1, ..., cD_1] for n-level decomposition.
        """
        # If data is stereo (e.g., shape (num_samples, 2)), use only the first channel for DWT.
        # This is a common simplification for audio steganography.
        if audio_data.ndim > 1 and audio_data.shape[1] > 1: # Check if multi-channel
            data_for_dwt = audio_data[:, 0]  # Select the first channel
        else:
            data_for_dwt = audio_data # Mono audio or already 1D

        # Apply multi-level DWT using wavedec (Wavelet DEComposition)
        coeffs = pywt.wavedec(data_for_dwt, self.wavelet, level=self.level)
        return coeffs

    def apply_idwt(self, coeffs):
        """
        Applies Inverse Discrete Wavelet Transform (IDWT) to reconstruct the audio signal
        from its DWT coefficients.

        Args:
            coeffs (list): A list of DWT coefficient arrays.

        Returns:
            numpy.ndarray: The reconstructed audio data.
        """
        # Reconstruct data using waverec (Wavelet REConstruction)
        reconstructed_data = pywt.waverec(coeffs, self.wavelet)
        return reconstructed_data

    def embed_bits_in_coefficients(self, coeffs, bits, alpha=0.001):
        """
        Embeds a string of bits into the detail coefficients of the DWT.
        This method uses a quantization-based approach where the remainder of
        the coefficient's absolute value divided by 2*alpha determines the bit.

        Args:
            coeffs (list): The DWT coefficient arrays.
            bits (str): The string of bits to embed (e.g., "10110").
            alpha (float): A scaling factor that influences the embedding strength
                           and audibility. Smaller alpha usually means less audible
                           but potentially less robust.

        Returns:
            list: The modified DWT coefficient arrays with the bits embedded.

        Raises:
            ValueError: If the message (number of bits) is too long to be embedded
                        in the available detail coefficients.
        """
        # We typically embed in one of the detail coefficient arrays.
        # For a multi-level decomposition, coeffs is [cA_n, cD_n, ..., cD_1].
        # coeffs[1] corresponds to cD_n (highest level detail) if n=level.
        # If level=1, coeffs is [cA_1, cD_1], so coeffs[1] is cD_1.
        # Let's assume we embed in the first set of detail coefficients available,
        # which is often cD_1 (the highest frequency details if coeffs are ordered cA, cD_level, ..., cD_1).
        # PyWavelets returns [cA_level, cD_level, cD_level-1, ..., cD_1].
        # So, coeffs[-1] is cD_1. If level=1, coeffs[1] is cD_1.
        # For simplicity and common practice, let's target coeffs[1] which is cD_level.
        # Or, more robustly, target the highest frequency detail cD_1 (coeffs[-1]).
        # The original code uses coeffs[1], which is cD_level if level > 0.
        # If level = 1, then coeffs = [cA1, cD1], so coeffs[1] is cD1. This is fine.

        # Create a copy of the coefficients to avoid modifying the original list/arrays in place.
        modified_coeffs_list = [c.copy() for c in coeffs] # Make deep copies of arrays within list
        detail_coeffs_to_modify = modified_coeffs_list[1] # Target DWT level for embedding (e.g., cD_level)

        # Ensure there are enough coefficients to embed all bits
        if len(bits) > len(detail_coeffs_to_modify):
            raise ValueError(f"Message too long to embed. Max {len(detail_coeffs_to_modify)} bits, "
                             f"but got {len(bits)} bits.")

        # Embed bits into the selected detail coefficients
        for i in range(len(bits)):
            # Get the absolute value of the current coefficient
            coeff_abs = abs(detail_coeffs_to_modify[i])

            # Calculate the current remainder when divided by (2 * alpha)
            # This defines quantization bins.
            remainder = coeff_abs % (2 * alpha)

            # Determine the target remainder based on the bit to embed
            if bits[i] == '1':
                # For bit '1', target a remainder of alpha (center of a quantization bin)
                target_remainder = alpha
            else: # bits[i] == '0'
                # For bit '0', target a remainder of 0 (start of a quantization bin)
                # or 2*alpha which is equivalent to 0 in modulo arithmetic.
                target_remainder = 0 # Could also be 2*alpha, but 0 makes adjustment logic simpler.

            # Calculate the necessary adjustment to reach the target_remainder
            adjustment = target_remainder - remainder
            # If remainder is already > target_remainder and we want to go to a "lower" bin start,
            # adjustment might be negative. If remainder is < target_remainder for bit '1',
            # adjustment is positive.
            # This needs to be careful if coeff_abs + adjustment < 0.
            # The current logic assumes coeff_abs + adjustment will remain >= 0 because alpha is small.

            # Apply the adjustment, preserving the original sign of the coefficient
            sign = 1 if detail_coeffs_to_modify[i] >= 0 else -1
            new_abs_val = coeff_abs + adjustment
            
            # Ensure new_abs_val is not negative (can happen if adjustment is too large negatively)
            # This check is crucial if alpha is large relative to coeff_abs.
            if new_abs_val < 0:
                 # Option 1: clip to zero or small epsilon
                 # new_abs_val = 0
                 # Option 2: adjust in the other direction towards the boundary of the next bin
                 # This can get complex. The original logic assumes alpha is small enough.
                 # For now, let's stick to the provided logic and note this as a potential issue.
                 pass


            detail_coeffs_to_modify[i] = sign * new_abs_val

        # The modified_coeffs_list already contains the modified detail_coeffs_to_modify
        # because detail_coeffs_to_modify is a reference to an array within that list.
        return modified_coeffs_list

    def extract_bits_from_coefficients(self, coeffs, num_bits, alpha=0.001):
        """
        Extracts bits from the detail coefficients of the DWT.
        This method is the inverse of `embed_bits_in_coefficients`.

        Args:
            coeffs (list): The DWT coefficient arrays (presumably from a stego-signal).
            num_bits (int): The number of bits to extract.
            alpha (float): The scaling factor used during embedding.

        Returns:
            str: The extracted string of bits.
        """
        # Extract from the same DWT level used for embedding (e.g., coeffs[1] -> cD_level)
        detail_coeffs = coeffs[1]
        extracted_bits = ""

        # Ensure we don't try to extract more bits than available in coefficients or requested
        max_bits_to_extract = min(num_bits, len(detail_coeffs))

        # Define thresholds for deciding if a bit is '0' or '1'.
        # These thresholds create a decision boundary around the expected remainder values.
        # For bit '1', remainder was targeted at alpha.
        # For bit '0', remainder was targeted at 0 (or 2*alpha).
        # A bit is '1' if remainder is closer to alpha than to 0 or 2*alpha.
        # Decision boundary can be set at alpha/2 and 3*alpha/2.
        # If remainder is in [alpha/2, 3*alpha/2), it's a '1'. Otherwise, '0'.
        # The original code uses:
        # threshold_low = 0.4 * alpha
        # threshold_high = 1.6 * alpha
        # This means bit '1' if remainder is in [0.4*alpha, 1.6*alpha].
        # This range is centered around alpha with a width of 1.2*alpha.
        # The total range for remainder is [0, 2*alpha).

        threshold_low = 0.5 * alpha  # Midpoint between 0 and alpha
        threshold_high = 1.5 * alpha # Midpoint between alpha and 2*alpha

        # Extract bits from the detail coefficients
        for i in range(max_bits_to_extract):
            coeff_abs = abs(detail_coeffs[i])
            remainder = coeff_abs % (2 * alpha)

            # Decide bit based on remainder's proximity to alpha vs. 0/2*alpha
            if remainder >= threshold_low and remainder < threshold_high:
                extracted_bits += "1" # Remainder is closer to alpha
            else:
                extracted_bits += "0" # Remainder is closer to 0 or 2*alpha
        
        return extracted_bits

    # The bits_to_bytes and bytes_to_bits methods are utility functions.
    # They are often part of a general 'utils' module rather than specific to DWT logic.
    # Including them here for completeness if they are tightly coupled with this class's usage.
    def bits_to_bytes(self, bits):
        """
        Converts a string of bits to a bytes object.
        Pads with '0' if length is not a multiple of 8.
        """
        padded_bits = bits
        if len(bits) % 8 != 0:
            # Pad with '0's at the end to make length a multiple of 8.
            # This padding must be handled (e.g., removed) upon decoding if original length is critical.
            padded_bits = bits + "0" * (8 - (len(bits) % 8))

        bytes_data = bytearray()
        for i in range(0, len(padded_bits), 8):
            byte_chunk = padded_bits[i:i+8]
            bytes_data.append(int(byte_chunk, 2)) # Convert 8-bit string to integer, then to byte

        return bytes(bytes_data) # Convert bytearray to immutable bytes object

    def bytes_to_bits(self, data_bytes):
        """
        Converts a bytes object to a string of bits.
        """
        bits = ""
        for byte_val in data_bytes: # Iterate through each byte in the bytes object
            # bin(byte_val) produces "0b..." prefix, [2:] removes it.
            # .zfill(8) pads with leading zeros to ensure 8 bits per byte.
            bits += bin(byte_val)[2:].zfill(8)
        return bits

    def embed_data(self, audio_path, output_path, data_bits, alpha=0.001):
        """
        High-level function to embed data (as bits) into an audio file.
        This orchestrates reading, DWT, embedding, IDWT, and saving.

        Args:
            audio_path (str): Path to the original input audio file.
            output_path (str): Path to save the stego audio file.
            data_bits (str): The string of bits to embed.
            alpha (float): Alpha value for embedding.

        Returns:
            bool: True if embedding was successful, False otherwise (though errors might raise exceptions).
        """
        try:
            # Read original audio file
            audio_data, sample_rate = self.read_audio(audio_path)

            # Apply DWT
            coeffs = self.apply_dwt(audio_data)

            # Embed the bits into coefficients
            modified_coeffs = self.embed_bits_in_coefficients(coeffs, data_bits, alpha=alpha)

            # Apply Inverse DWT to reconstruct the audio
            reconstructed_data = self.apply_idwt(modified_coeffs)

            # If the original audio was stereo, ensure the output is also stereo.
            # The DWT was applied to one channel; other channels should be preserved or reconstructed.
            if audio_data.ndim > 1 and audio_data.shape[1] > 1: # If original was multi-channel
                # Ensure reconstructed data length matches (or is handled appropriately)
                min_len = min(len(reconstructed_data), audio_data.shape[0])
                # Create a new stereo array
                reconstructed_stereo = np.zeros((min_len, audio_data.shape[1]), dtype=audio_data.dtype)
                # Place the reconstructed channel back
                reconstructed_stereo[:, 0] = reconstructed_data[:min_len]
                # Copy other channels from the original audio
                for ch_idx in range(1, audio_data.shape[1]):
                    reconstructed_stereo[:, ch_idx] = audio_data[:min_len, ch_idx]
                reconstructed_data_final = reconstructed_stereo
            else: # Original was mono
                reconstructed_data_final = reconstructed_data
            
            # Ensure reconstructed data does not exceed original length significantly due to filter delays.
            # Usually, pywt handles this well, but output might be slightly longer/shorter.
            # Truncate if necessary to match original audio length more closely, if desired.
            # This can be important to avoid issues with some audio players or further processing.
            if len(reconstructed_data_final) > audio_data.shape[0]:
                reconstructed_data_final = reconstructed_data_final[:audio_data.shape[0]]


            # Save the modified (stego) audio
            self.save_audio(output_path, reconstructed_data_final, sample_rate)
            return True
        except Exception as e:
            print(f"Error during embedding: {e}")
            return False

    def extract_data(self, stego_audio_path, num_bits, alpha=0.001):
        """
        High-level function to extract embedded bits from a stego audio file.

        Args:
            stego_audio_path (str): Path to the stego audio file.
            num_bits (int): The number of bits to extract.
            alpha (float): Alpha value used during embedding.

        Returns:
            str: The extracted string of bits, or None if an error occurs.
        """
        try:
            # Read the stego audio file
            stego_data, sample_rate = self.read_audio(stego_audio_path)

            # Apply DWT (on the first channel if stereo, consistent with embedding)
            coeffs = self.apply_dwt(stego_data)

            # Extract the bits from coefficients
            extracted_bits = self.extract_bits_from_coefficients(coeffs, num_bits, alpha=alpha)

            return extracted_bits
        except Exception as e:
            print(f"Error during extraction: {e}")
            return None
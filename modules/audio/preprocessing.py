# ciel/modules/audio/preprocessing.py
from typing import Dict
import numpy as np
from typing import Optional, Tuple
from scipy import signal

class AudioPreprocessor:
    """Audio preprocessing and enhancement"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        
        # Preprocessing settings
        self.noise_reduction_enabled = True
        self.dc_removal_enabled = True
        self.normalization_enabled = True
        
        # Filter parameters
        self.low_cut = 80  # Hz
        self.high_cut = 7000  # Hz
        self.order = 4
        
        # Initialize filters
        self._init_filters()

    def _init_filters(self):
        """Initialize audio filters"""
        nyquist = self.sample_rate / 2
        low = self.low_cut / nyquist
        high = self.high_cut / nyquist
        self.b, self.a = signal.butter(self.order, [low, high], btype='band')

    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Process audio data with all enabled enhancements
        
        Args:
            audio_data: Input audio array
            
        Returns:
            Processed audio array
        """
        if audio_data.size == 0:
            return audio_data
            
        # Apply DC offset removal
        if self.dc_removal_enabled:
            audio_data = self._remove_dc_offset(audio_data)
            
        # Apply bandpass filter
        audio_data = self._apply_bandpass(audio_data)
        
        # Apply noise reduction
        if self.noise_reduction_enabled:
            audio_data = self._reduce_noise(audio_data)
            
        # Apply normalization
        if self.normalization_enabled:
            audio_data = self._normalize(audio_data)
            
        return audio_data

    def _remove_dc_offset(self, audio_data: np.ndarray) -> np.ndarray:
        """Remove DC offset from audio"""
        return audio_data - np.mean(audio_data)

    def _apply_bandpass(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply bandpass filter"""
        return signal.filtfilt(self.b, self.a, audio_data)

    def _reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Basic noise reduction using spectral subtraction"""
        # Estimate noise from the first 100ms
        noise_sample = audio_data[:int(self.sample_rate * 0.1)]
        noise_profile = np.mean(np.abs(noise_sample))
        
        # Apply noise gate
        audio_data = np.where(
            np.abs(audio_data) < noise_profile * 2,
            np.zeros_like(audio_data),
            audio_data
        )
        
        return audio_data

    def _normalize(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val
        return audio_data

    def get_signal_stats(self, audio_data: np.ndarray) -> Dict:
        """Get audio signal statistics"""
        return {
            'rms': np.sqrt(np.mean(np.square(audio_data))),
            'peak': np.max(np.abs(audio_data)),
            'zero_crossings': np.sum(np.diff(np.signbit(audio_data))),
            'duration': len(audio_data) / self.sample_rate
        }
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any

class BackendUtils:
    """Utility functions for vision backends"""
    
    @staticmethod
    def resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Resize frame while maintaining aspect ratio
        
        Args:
            frame: Input frame
            width: Target width
            height: Target height
            
        Returns:
            Resized frame
        """
        if frame is None:
            return None
            
        aspect = frame.shape[1] / frame.shape[0]
        if width / height > aspect:
            new_width = int(height * aspect)
            new_height = height
        else:
            new_width = width
            new_height = int(width / aspect)
            
        return cv2.resize(frame, (new_width, new_height))

    @staticmethod
    def normalize_frame(frame: np.ndarray) -> np.ndarray:
        """
        Normalize frame values to [0, 1] range
        
        Args:
            frame: Input frame
            
        Returns:
            Normalized frame
        """
        return frame.astype(np.float32) / 255.0

    @staticmethod
    def denormalize_frame(frame: np.ndarray) -> np.ndarray:
        """
        Convert normalized frame back to uint8
        
        Args:
            frame: Normalized frame
            
        Returns:
            Denormalized frame
        """
        return (frame * 255).astype(np.uint8)

    @staticmethod
    def apply_color_correction(
        frame: np.ndarray,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0
    ) -> np.ndarray:
        """
        Apply color correction to frame
        
        Args:
            frame: Input frame
            brightness: Brightness adjustment factor
            contrast: Contrast adjustment factor
            saturation: Saturation adjustment factor
            
        Returns:
            Color corrected frame
        """
        # Convert to float
        frame_float = frame.astype(np.float32) / 255.0
        
        # Adjust brightness
        frame_float = frame_float * brightness
        
        # Adjust contrast
        frame_float = (frame_float - 0.5) * contrast + 0.5
        
        # Adjust saturation
        if saturation != 1.0:
            hsv = cv2.cvtColor(frame_float, cv2.COLOR_BGR2HSV)
            hsv[..., 1] = hsv[..., 1] * saturation
            frame_float = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Clip and convert back to uint8
        frame_float = np.clip(frame_float, 0, 1)
        return (frame_float * 255).astype(np.uint8)

    @staticmethod
    def detect_blur(frame: np.ndarray, threshold: float = 100.0) -> Tuple[bool, float]:
        """
        Detect if frame is blurry
        
        Args:
            frame: Input frame
            threshold: Blur detection threshold
            
        Returns:
            Tuple of (is_blurry, blur_score)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        return score < threshold, score

    @staticmethod
    def get_frame_metrics(frame: np.ndarray) -> Dict[str, Any]:
        """
        Calculate various frame metrics
        
        Args:
            frame: Input frame
            
        Returns:
            Dictionary of metrics
        """
        if frame is None:
            return {}
            
        metrics = {
            'shape': frame.shape,
            'mean': np.mean(frame, axis=(0, 1)).tolist(),
            'std': np.std(frame, axis=(0, 1)).tolist(),
            'min': np.min(frame, axis=(0, 1)).tolist(),
            'max': np.max(frame, axis=(0, 1)).tolist(),
            'is_blurry': None,
            'blur_score': None
        }
        
        # Add blur detection
        metrics['is_blurry'], metrics['blur_score'] = BackendUtils.detect_blur(frame)
        
        return metrics
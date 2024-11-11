import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
import logging

class VisionBackend(ABC):
    """Abstract base class for vision processing backends"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._initialized = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the backend"""
        pass

    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> Tuple[bool, np.ndarray, Dict[str, Any]]:
        """
        Process a single frame
        
        Args:
            frame: Input frame as numpy array
            
        Returns:
            Tuple containing:
            - Success flag (bool)
            - Processed frame (numpy array)
            - Metadata dictionary
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Cleanup resources"""
        pass

class CoreMLBackend(VisionBackend):
    """Vision backend using CoreML for macOS"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.model = None
        self.input_shape = None
        
        # Check if we're on macOS
        import platform
        if platform.system() != 'Darwin':
            raise RuntimeError("CoreML backend is only available on macOS")

    def initialize(self) -> bool:
        try:
            # Import CoreML modules
            import coremltools as ct
            
            # Load model if specified in config
            model_path = self.config.get('model_path')
            if model_path:
                self.model = ct.models.MLModel(model_path)
                self.input_shape = self.model.get_spec().description.input[0].type.imageType.height
                self.logger.info(f"CoreML model loaded from {model_path}")
            
            self._initialized = True
            return True
            
        except ImportError:
            self.logger.error("CoreML dependencies not available")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize CoreML backend: {e}")
            return False

    def process_frame(self, frame: np.ndarray) -> Tuple[bool, np.ndarray, Dict[str, Any]]:
        if not self._initialized:
            return False, frame, {"error": "Backend not initialized"}
            
        try:
            # Basic preprocessing
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Apply CoreML model if loaded
            metadata = {}
            if self.model:
                # Resize if needed
                if self.input_shape:
                    processed_frame = cv2.resize(processed_frame, (self.input_shape, self.input_shape))
                
                # Run inference
                results = self.model.predict({'image': processed_frame})
                metadata['predictions'] = results
            
            return True, processed_frame, metadata
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {e}")
            return False, frame, {"error": str(e)}

    def cleanup(self):
        """Cleanup CoreML resources"""
        self.model = None
        self._initialized = False

class CPUBackend(VisionBackend):
    """Basic CPU-based vision backend"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.face_cascade = None
        self.background_subtractor = None

    def initialize(self) -> bool:
        try:
            # Initialize OpenCV components
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Initialize background subtraction
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=500,
                varThreshold=16,
                detectShadows=True
            )
            
            self._initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CPU backend: {e}")
            return False

    def process_frame(self, frame: np.ndarray) -> Tuple[bool, np.ndarray, Dict[str, Any]]:
        if not self._initialized:
            return False, frame, {"error": "Backend not initialized"}
            
        try:
            metadata = {}
            processed_frame = frame.copy()
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw faces and add to metadata
            metadata['faces'] = []
            for (x, y, w, h) in faces:
                cv2.rectangle(processed_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                metadata['faces'].append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                })
            
            # Apply background subtraction
            fg_mask = self.background_subtractor.apply(frame)
            metadata['motion_detected'] = np.mean(fg_mask) > 10
            
            # Add processing stats
            metadata['frame_info'] = {
                'shape': frame.shape,
                'dtype': str(frame.dtype),
                'faces_detected': len(faces)
            }
            
            return True, processed_frame, metadata
            
        except Exception as e:
            self.logger.error(f"Frame processing error: {e}")
            return False, frame, {"error": str(e)}

    def cleanup(self):
        """Cleanup CPU backend resources"""
        self.face_cascade = None
        self.background_subtractor = None
        self._initialized = False

# Optional: GPU backend if needed
class GPUBackend(VisionBackend):
    """GPU-accelerated vision backend (placeholder)"""
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.logger.warning("GPU backend is not fully implemented yet")

    def initialize(self) -> bool:
        self.logger.warning("GPU backend initialization not implemented")
        return False

    def process_frame(self, frame: np.ndarray) -> Tuple[bool, np.ndarray, Dict[str, Any]]:
        return False, frame, {"error": "GPU backend not implemented"}

    def cleanup(self):
        pass

# Backend factory
def create_backend(backend_type: str, config: Dict[str, Any], logger: Optional[logging.Logger] = None) -> VisionBackend:
    """
    Create a vision backend instance
    
    Args:
        backend_type: Type of backend ('coreml', 'cpu', or 'gpu')
        config: Backend configuration
        logger: Optional logger instance
        
    Returns:
        VisionBackend instance
    """
    backends = {
        'coreml': CoreMLBackend,
        'cpu': CPUBackend,
        'gpu': GPUBackend
    }
    
    if backend_type not in backends:
        raise ValueError(f"Unknown backend type: {backend_type}")
        
    return backends[backend_type](config, logger)
# core/config.py
from dataclasses import dataclass, field
from typing import Optional, Dict
from pathlib import Path
import os

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class AudioConfig:
    """Comprehensive audio configuration"""
    
    # Basic audio settings
    sample_rate: int = 16000
    channels: int = 1
    language: str = 'fr'
    enabled: bool = True
    
    # TTS settings
    tts_engine: str = "pyttsx3"  # Options: "pyttsx3", "edge-tts"
    tts_voice: str = "fr-FR-HenriNeural"  # Default voice for Edge TTS
    tts_rate: int = 175  # Speech rate (words per minute)
    tts_volume: float = 1.0  # Volume level (0.0 to 1.0)
    tts_pitch: int = 100  # Voice pitch (50 to 200)
    
    # Edge TTS specific settings
    edge_tts_voice_options: Dict[str, str] = field(default_factory=lambda: {
        'fr': 'fr-FR-HenriNeural',
        'en': 'en-US-ChristopherNeural',
        'es': 'es-ES-AlvaroNeural',
        'de': 'de-DE-ConradNeural',
        'it': 'it-IT-DiegoNeural'
    })
    
    # pyttsx3 specific settings
    pyttsx3_voice_id: Optional[str] = None  # System-specific voice ID
    
    # Audio processing settings
    chunk_size: int = 1024  # Audio chunk size for processing
    format: str = 'float32'  # Audio format ('int16', 'float32')
    input_device: Optional[int] = None  # Input device index
    output_device: Optional[int] = None  # Output device index
    
    # Voice Activity Detection (VAD) settings
    vad_enabled: bool = True
    vad_mode: int = 3  # VAD aggressiveness (0-3)
    vad_frame_duration: int = 30  # Frame duration in ms (10, 20, or 30)
    min_speech_duration: float = 0.3  # Minimum speech duration in seconds
    silence_duration: float = 0.5  # Silence duration to stop recording
    
    # Speech Recognition settings
    recognition_enabled: bool = True
    recognition_language: str = 'fr-FR'
    recognition_timeout: float = 10.0  # Recognition timeout in seconds
    recognition_energy_threshold: float = 300  # Energy level threshold
    recognition_dynamic_energy: bool = True  # Dynamic energy threshold
    
    # Audio enhancement settings
    noise_reduction: bool = True
    echo_cancellation: bool = True
    automatic_gain: bool = True
    volume_normalization: bool = True
    
    # Performance settings
    buffer_size: int = 4096
    processing_threads: int = 2
    low_latency: bool = True
    
    # Error handling settings
    max_retries: int = 3
    retry_delay: float = 1.0  # Delay between retries in seconds
    fallback_enabled: bool = True
    
    # Logging settings
    debug_logging: bool = False
    log_audio_stats: bool = True
    log_interval: int = 100  # Log interval in frames
    
    def __post_init__(self):
        """Validate and adjust configuration after initialization"""
        # Validate sample rate
        valid_sample_rates = [8000, 16000, 32000, 44100, 48000]
        if self.sample_rate not in valid_sample_rates:
            raise ValueError(f"Invalid sample rate. Must be one of {valid_sample_rates}")
        
        # Validate VAD frame duration
        valid_frame_durations = [10, 20, 30]
        if self.vad_frame_duration not in valid_frame_durations:
            raise ValueError(f"Invalid VAD frame duration. Must be one of {valid_frame_durations}")
        
        # Validate VAD mode
        if not 0 <= self.vad_mode <= 3:
            raise ValueError("VAD mode must be between 0 and 3")
        
        # Validate volume
        if not 0.0 <= self.tts_volume <= 1.0:
            raise ValueError("TTS volume must be between 0.0 and 1.0")
        
        # Validate pitch
        if not 50 <= self.tts_pitch <= 200:
            raise ValueError("TTS pitch must be between 50 and 200")
        
        # Calculate derived values
        self.blocksize = int(self.sample_rate * self.vad_frame_duration / 1000)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            key: getattr(self, key) 
            for key in self.__annotations__
            if hasattr(self, key)
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AudioConfig':
        """Create configuration from dictionary"""
        return cls(**config_dict)
    
    def validate_devices(self) -> bool:
        """Validate audio devices"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            
            # Validate input device
            if self.input_device is not None:
                if self.input_device >= len(devices):
                    raise ValueError(f"Invalid input device index: {self.input_device}")
                device = devices[self.input_device]
                if device['max_input_channels'] == 0:
                    raise ValueError(f"Device {self.input_device} does not support input")
            
            # Validate output device
            if self.output_device is not None:
                if self.output_device >= len(devices):
                    raise ValueError(f"Invalid output device index: {self.output_device}")
                device = devices[self.output_device]
                if device['max_output_channels'] == 0:
                    raise ValueError(f"Device {self.output_device} does not support output")
                    
            return True
            
        except Exception as e:
            print(f"Device validation failed: {e}")
            return False
    
    def get_tts_voice(self, language: Optional[str] = None) -> str:
        """Get appropriate TTS voice for language"""
        lang = language or self.language
        if self.tts_engine == "edge-tts":
            return self.edge_tts_voice_options.get(lang, self.tts_voice)
        return self.pyttsx3_voice_id or self.tts_voice
    
    def optimize_for_capability(self, capability: str):
        """Optimize settings for specific capability"""
        if capability == "speed":
            self.buffer_size = 2048
            self.low_latency = True
            self.processing_threads = 1
            self.format = 'int16'
        elif capability == "quality":
            self.buffer_size = 4096
            self.low_latency = False
            self.processing_threads = 2
            self.format = 'float32'
        elif capability == "reliability":
            self.max_retries = 5
            self.fallback_enabled = True
            self.retry_delay = 2.0

# Basic usage
config = AudioConfig()

# Custom configuration
config = AudioConfig(
    language='fr',
    tts_engine='edge-tts',
    tts_rate=150,
    vad_mode=2
)

# Optimize for specific use case
config.optimize_for_capability('speed')

# Validate devices
if config.validate_devices():
    print("Audio devices configured correctly")

# Get configuration as dictionary
config_dict = config.to_dict()

@dataclass
class VisionConfig:
    """Vision module configuration"""
    enabled: bool = True
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    fps: int = 30

@dataclass
class ConversationConfig:
    """Conversation module configuration"""
    max_history: int = 10
    context_window: int = 5
    language: str = 'fr'
    response_timeout: float = 5.0

@dataclass
class SystemConfig:
    """System-wide configuration"""
    debug: bool = False
    log_level: str = 'INFO'
    data_dir: Path = field(default_factory=lambda: Path('data'))
    model_dir: Path = field(default_factory=lambda: Path('models'))
    log_dir: Path = field(default_factory=lambda: Path('logs'))

@dataclass
class Config:
    """Main configuration class"""
    audio: AudioConfig = field(default_factory=AudioConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    def __post_init__(self):
        """Create necessary directories after initialization"""
        # Create system directories
        self.system.data_dir.mkdir(parents=True, exist_ok=True)
        self.system.model_dir.mkdir(parents=True, exist_ok=True)
        self.system.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set model path if not specified
        if self.audio.model_path is None:
            self.audio.model_path = str(self.system.model_dir / f"vosk-model-{self.audio.model_lang}")
    
    def save(self, path: str = "config.json"):
        """Save configuration to file"""
        import json
        
        def _to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {k: _to_dict(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, Path):
                return str(obj)
            return obj
        
        with open(path, 'w') as f:
            json.dump(_to_dict(self), f, indent=2)
    
    @classmethod
    def load(cls, path: str = "config.json") -> 'Config':
        """Load configuration from file"""
        import json
        
        def _from_dict(data: Dict) -> Config:
            config = cls()
            
            def _update_dataclass(obj, data):
                for k, v in data.items():
                    if hasattr(obj, k):
                        if isinstance(getattr(obj, k), Path):
                            setattr(obj, k, Path(v))
                        elif isinstance(v, dict) and hasattr(getattr(obj, k), '__dict__'):
                            _update_dataclass(getattr(obj, k), v)
                        else:
                            setattr(obj, k, v)
            
            _update_dataclass(config, data)
            return config
        
        try:
            with open(path) as f:
                return _from_dict(json.load(f))
        except FileNotFoundError:
            return cls()
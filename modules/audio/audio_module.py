from dataclasses import dataclass
from typing import Optional, Dict, Any
from queue import Queue
import threading
import numpy as np
import sounddevice as sd
import time
import logging
import torch
from TTS.api import TTS

@dataclass
class TTSConfig:
    """TTS Configuration"""
    model_name: str = "tts_models/en/vctk/vits"
    speaker: str = "p273"  # VCTK speaker ID
    language: str = "en"
    rate: float = 1.0  # Speed multiplier
    volume: float = 1.0

class TTSEngine:
    """TTS Engine using Coqui TTS"""
    
    def __init__(self, config: TTSConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._audio_queue = Queue()
        self._is_speaking = False
        
        # Initialize Coqui TTS
        self._init_tts()
        
    def _init_tts(self):
        """Initialize Coqui TTS engine"""
        try:
            # Use MPS (Metal) for M1 Macs if available
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            self.logger.info(f"Using device: {device}")
            
            # Initialize TTS with the specified model
            self.engine = TTS(model_name=self.config.model_name, progress_bar=False)
            self.engine.to(device)
            
            self.logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Coqui TTS: {e}")
            raise
            
    def _play_audio(self, wav: np.ndarray, sample_rate: int):
        """Play audio using sounddevice"""
        try:
            # Apply volume adjustment
            wav = wav * self.config.volume
            
            # Play the audio
            sd.play(wav, sample_rate, blocking=True)
            sd.wait()
            
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
                
    def speak(self, text: str):
        """Speak text using Coqui TTS"""
        if not text:
            return
            
        try:
            # Generate audio
            wav = self.engine.tts(
                text=text,
                speaker=self.config.speaker,
                language=self.config.language,
                speed=self.config.rate
            )
            
            # Get the sample rate from the model
            sample_rate = self.engine.synthesizer.output_sample_rate
            
            # Play the audio
            self._play_audio(wav, sample_rate)
                
        except Exception as e:
            self.logger.error(f"Error in TTS: {e}")

class AudioModule(BaseModule):
    """Enhanced audio module with TTS support"""
    
    def __init__(self, config, event_bus, logger=None, db_manager=None):
        """Initialize audio module"""
        super().__init__(logger)
        
        # Core components
        self.config = config
        self.event_bus = event_bus
        
        # TTS Configuration
        self.tts_config = TTSConfig(
            model_name=getattr(config, 'tts_model', 'tts_models/en/vctk/vits'),
            speaker=getattr(config, 'tts_speaker', 'p273'),
            language=getattr(config, 'tts_language', 'en'),
            rate=getattr(config, 'tts_rate', 1.0),
            volume=getattr(config, 'tts_volume', 1.0)
        )
        
        # Initialize TTS engine
        self.tts_engine = None
        self.audio_queue = Queue()
        
        # State tracking
        self.is_speaking = False
        self.current_text = None
        
    def _initialize(self) -> bool:
        """Initialize module"""
        try:
            # Initialize TTS engine
            self.tts_engine = TTSEngine(self.tts_config, self.logger)
            
            # Subscribe to speech events
            self.event_bus.subscribe(EventTypes.SPEECH_OUTPUT, self._handle_speech_output)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize audio module: {e}")
            return False
            
    def _handle_speech_output(self, event: Any):
        """Handle speech output events"""
        if not event.data or 'text' not in event.data:
            return
            
        text = event.data['text']
        self.speak(text)
        
    def speak(self, text: str):
        """Speak text using TTS engine"""
        if self.is_speaking:
            self.audio_queue.put(text)
            return
            
        try:
            self.is_speaking = True
            self.current_text = text
            
            # Speak current text
            self.tts_engine.speak(text)
            
            # Process queue
            while not self.audio_queue.empty():
                next_text = self.audio_queue.get()
                self.tts_engine.speak(next_text)
                
        finally:
            self.is_speaking = False
            self.current_text = None
            
    def stop(self):
        """Stop audio processing"""
        self.is_speaking = False
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Queue.Empty:
                break
        super().stop()
        
    def cleanup(self):
        """Clean up resources"""
        self.stop()
        if hasattr(self, 'tts_engine'):
            del self.tts_engine
        self.logger.info("Audio module cleaned up")
        
    def get_status(self) -> Dict:
        """Get module status"""
        status = super().get_status()
        status.update({
            'is_speaking': self.is_speaking,
            'current_text': self.current_text,
            'queue_size': self.audio_queue.qsize()
        })
        return status
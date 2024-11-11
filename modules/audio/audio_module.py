import pyttsx3
import asyncio
import edge_tts
from dataclasses import dataclass
from typing import Optional, Dict, Any
from queue import Queue
import threading
import numpy as np
import sounddevice as sd
import time
import logging


@dataclass
class TTSConfig:
    """TTS Configuration"""
    engine: str = "pyttsx3"  # "pyttsx3" or "edge-tts"
    voice: str = "fr-FR-HenriNeural"  # For edge-tts
    rate: int = 175
    volume: float = 1.0
    pitch: int = 100

class TTSEngine:
    """TTS Engine wrapper supporting multiple backends"""
    
    def __init__(self, config: TTSConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.engine = None
        self._audio_queue = Queue()
        self._is_speaking = False
        
        if config.engine == "pyttsx3":
            self._init_pyttsx3()
        elif config.engine == "edge-tts":
            self._init_edge_tts()
        else:
            raise ValueError(f"Unsupported TTS engine: {config.engine}")
            
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.config.rate)
            self.engine.setProperty('volume', self.config.volume)
            
            # Set French voice if available
            voices = self.engine.getProperty('voices')
            french_voice = next((v for v in voices if 'fr' in v.id.lower()), None)
            if french_voice:
                self.engine.setProperty('voice', french_voice.id)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize pyttsx3: {e}")
            raise
            
    def _init_edge_tts(self):
        """Initialize edge-tts"""
        self.communicate = edge_tts.Communicate
        
    async def _edge_tts_speak(self, text: str):
        """Edge TTS speak implementation"""
        try:
            communicate = self.communicate(text, self.config.voice)
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    self._audio_queue.put(chunk["data"])
                    
        except Exception as e:
            self.logger.error(f"Edge TTS error: {e}")
            
    def _play_audio(self):
        """Play audio from queue"""
        while not self._audio_queue.empty():
            try:
                audio_data = self._audio_queue.get()
                sd.play(audio_data, blocking=True)
            except Exception as e:
                self.logger.error(f"Error playing audio: {e}")
                
    def speak(self, text: str):
        """Speak text using configured engine"""
        if not text:
            return
            
        try:
            if self.config.engine == "pyttsx3":
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                asyncio.run(self._edge_tts_speak(text))
                self._play_audio()
                
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
            engine=getattr(config, 'tts_engine', 'pyttsx3'),
            voice=getattr(config, 'tts_voice', 'fr-FR-HenriNeural'),
            rate=getattr(config, 'tts_rate', 175),
            volume=getattr(config, 'tts_volume', 1.0),
            pitch=getattr(config, 'tts_pitch', 100)
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
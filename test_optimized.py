import os
import sys
import logging
from core.events import EventBus
from modules.vision.vision_module import VisionModule
from modules.audio.audio_module import AudioModule, TTSConfig
from dataclasses import dataclass

@dataclass
class Config:
    """Simple config for testing"""
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    fps: int = 30
    
    # TTS settings
    tts_model: str = "tts_models/en/vctk/vits"
    tts_speaker: str = "p273"
    tts_language: str = "en"
    tts_rate: float = 1.0
    tts_volume: float = 1.0

def setup_logging():
    """Set up basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('Test')

def main():
    logger = setup_logging()
    event_bus = EventBus()
    config = Config()
    
    try:
        # Initialize vision module
        logger.info("Initializing Vision Module...")
        vision = VisionModule(config=config, logger=logger, event_bus=event_bus)
        
        # Initialize audio module
        logger.info("Initializing Audio Module...")
        audio = AudioModule(config=config, event_bus=event_bus, logger=logger)
        
        # Start vision module
        vision.start()
        
        # Test TTS
        logger.info("Testing TTS...")
        audio.speak("Hello! I am now using Coqui TTS for speech synthesis. "
                   "I can detect objects, faces, and hand gestures using the camera.")
        
        # Keep running until 'q' is pressed
        logger.info("Press 'q' in the video window to quit")
        while vision.running:
            pass
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
    finally:
        # Cleanup
        if 'vision' in locals():
            vision.stop()
        if 'audio' in locals():
            audio.stop()
        logger.info("Test completed")

if __name__ == "__main__":
    main()
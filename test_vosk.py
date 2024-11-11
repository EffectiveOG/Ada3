# test_vosk_model.py
import logging
import sys
from pathlib import Path
import wave
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def test_model():
    from modules.audio.model_manager import VoskModelManager
    try:
        from vosk import Model, KaldiRecognizer
    except ImportError:
        print("Please install vosk first: pip install vosk")
        return
    
    print("\nTesting Vosk model download and initialization...")
    
    # Initialize model manager
    manager = VoskModelManager()
    
    # Download model
    success, message = manager.download_model('fr')
    print(f"\nDownload result: {'Success' if success else 'Failed'}")
    print(f"Message: {message}")
    
    if success:
        model_path = manager.get_model_path('fr')
        print(f"\nModel path: {model_path}")
        
        try:
            # Try to initialize Vosk with the model
            model = Model(str(model_path))
            rec = KaldiRecognizer(model, 16000)
            print("\nSuccessfully initialized Vosk model!")
            
            # Print model info
            print("\nModel information:")
            if (model_path / "README").exists():
                with open(model_path / "README") as f:
                    print(f.read())
            
        except Exception as e:
            print(f"\nError initializing Vosk model: {e}")

if __name__ == "__main__":
    test_model()
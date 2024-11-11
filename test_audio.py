import sounddevice as sd
import numpy as np
import threading
import queue
import time

def test_audio_devices():
    """Test audio device enumeration and capabilities"""
    print("\nAudio Device Test")
    print("-" * 50)
    
    try:
        devices = sd.query_devices()
        print("\nAvailable Audio Devices:")
        for i, device in enumerate(devices):
            print(f"\nDevice {i}: {device['name']}")
            print(f"  Input channels: {device['max_input_channels']}")
            print(f"  Output channels: {device['max_output_channels']}")
            print(f"  Default samplerates: {device['default_samplerate']}")
            
        default_input = sd.query_devices(kind='input')
        print(f"\nDefault Input Device:")
        print(f"  {default_input['name']}")
        
        return True
        
    except Exception as e:
        print(f"Error testing audio devices: {e}")
        return False

def test_audio_recording():
    """Test audio recording capabilities"""
    print("\nAudio Recording Test")
    print("-" * 50)
    
    # Audio parameters
    samplerate = 16000
    channels = 1
    duration = 3  # seconds
    
    # Create a queue for audio data
    audio_queue = queue.Queue()
    recording = True
    
    def audio_callback(indata, frames, time, status):
        if status:
            print(f"Status: {status}")
        audio_queue.put(indata.copy())
    
    try:
        # Start recording
        print(f"\nRecording for {duration} seconds...")
        
        with sd.InputStream(
            samplerate=samplerate,
            channels=channels,
            callback=audio_callback
        ):
            time.sleep(duration)
        
        print("Recording completed!")
        return True
        
    except Exception as e:
        print(f"Error testing audio recording: {e}")
        return False

def main():
    """Run all audio tests"""
    print("Starting Audio System Tests")
    print("=" * 50)
    
    # Test audio devices
    devices_ok = test_audio_devices()
    
    # Test recording
    if devices_ok:
        recording_ok = test_audio_recording()
    
    print("\nTest Results:")
    print(f"Devices Test: {'✓' if devices_ok else '✗'}")
    print(f"Recording Test: {'✓' if recording_ok else '✗'}")
    
if __name__ == "__main__":
    main()
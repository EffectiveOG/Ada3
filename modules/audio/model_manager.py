# ciel/modules/audio/model_manager.py
import os
import requests
import zipfile
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict
import json
import logging
from datetime import datetime
from tqdm.auto import tqdm
import shutil

class VoskModelManager:
    """Manages Vosk model downloads and verification"""
    
    MODELS = {
        'fr': {
            'sources': [
                {
                    'url': 'https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip',
                    'size': '39M',
                    'version': '0.22',
                    'dir_prefix': 'vosk-model-small-fr-0.22'
                }
            ],
            'min_size_mb': 35,
            'max_size_mb': 45
        },
        'en': {
            'sources': [
                {
                    'url': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
                    'size': '40M',
                    'version': '0.15',
                    'dir_prefix': 'vosk-model-small-en-us-0.15'
                }
            ],
            'min_size_mb': 35,
            'max_size_mb': 45
        }
    }

    def __init__(self, base_path: Optional[str] = None):
        """Initialize model manager"""
        self.logger = logging.getLogger(__name__)
        
        if base_path is None:
            base_path = os.path.join(os.path.dirname(__file__), "models")
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.model_info_path = self.base_path / "model_info.json"
        self.model_info = self._load_model_info()
        
        # Create a session for downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _verify_existing_model(self, language: str) -> bool:
        """Verify if a valid model already exists"""
        try:
            model_path = self.base_path / f"vosk-model-{language}"
            if not model_path.exists():
                return False

            # Check required directories
            required_dirs = ['am', 'conf', 'graph', 'ivector']
            for dir_name in required_dirs:
                if not (model_path / dir_name).is_dir():
                    return False

            # Check required files
            required_files = [
                'conf/mfcc.conf',
                'am/final.mdl',
                'graph/HCLr.fst',
                'graph/Gr.fst',
                'conf/model.conf'
            ]
            
            for file_path in required_files:
                full_path = model_path / file_path
                if not full_path.is_file() or full_path.stat().st_size == 0:
                    return False

            # Update model info if valid but not in info file
            if language not in self.model_info:
                version = "unknown"
                for source in self.MODELS[language]['sources']:
                    if (model_path / 'README').exists():
                        version = source.get('version', 'unknown')
                        break
                
                self.model_info[language] = {
                    'path': str(model_path),
                    'version': version,
                    'date_downloaded': str(datetime.now())
                }
                self._save_model_info()

            self.logger.info(f"Found valid existing model for language: {language}")
            return True

        except Exception as e:
            self.logger.error(f"Error verifying existing model: {e}")
            return False

    def download_model(self, language: str = 'fr') -> Tuple[bool, str]:
        """Download and verify a Vosk model"""
        if language not in self.MODELS:
            return False, f"Unsupported language: {language}"

        # Check if valid model already exists
        if self._verify_existing_model(language):
            return True, "Using existing verified model"
            
        model_info = self.MODELS[language]
        final_model_path = self.base_path / f"vosk-model-{language}"
        download_path = self.base_path / f"model-{language}.zip"
        extract_path = self.base_path / "temp_extract"
        
        try:
            # Clean up any existing invalid files
            self._cleanup_files(final_model_path, download_path, extract_path)
            
            # Create temporary extraction directory
            extract_path.mkdir(exist_ok=True)
            
            # Try each source
            for source in model_info['sources']:
                self.logger.info(f"Downloading model for language: {language}")
                if not self._download_with_progress(source['url'], download_path, f"Downloading {language} model"):
                    continue

                try:
                    # Extract to temporary directory
                    self.logger.info("Extracting model...")
                    with zipfile.ZipFile(download_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)
                    
                    # Find the extracted model directory
                    extracted_dir = extract_path / source['dir_prefix']
                    if not extracted_dir.exists():
                        # Try to find the correct directory
                        possible_dirs = [d for d in extract_path.iterdir() if d.is_dir()]
                        if len(possible_dirs) == 1:
                            extracted_dir = possible_dirs[0]
                        else:
                            self.logger.error(f"Cannot determine model directory. Found: {[d.name for d in possible_dirs]}")
                            continue
                    
                    # Move to final location
                    if final_model_path.exists():
                        shutil.rmtree(final_model_path)
                    shutil.move(str(extracted_dir), str(final_model_path))
                    
                    # Verify moved model
                    if self._verify_existing_model(language):
                        # Cleanup
                        self._cleanup_files(None, download_path, extract_path)
                        return True, "Model downloaded and verified successfully"
                    else:
                        self.logger.error("Model verification failed after extraction")
                        
                except Exception as e:
                    self.logger.error(f"Error processing model: {e}")
                    continue
                    
            return False, "Failed to download and verify model"
            
        except Exception as e:
            self.logger.error(f"Error downloading model: {e}")
            self._cleanup_files(final_model_path, download_path, extract_path)
            return False, str(e)

    def _load_model_info(self) -> Dict:
        """Load model information from disk"""
        if self.model_info_path.exists():
            try:
                with open(self.model_info_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading model info: {e}")
        return {}

    def _save_model_info(self):
        """Save model information to disk"""
        try:
            with open(self.model_info_path, 'w') as f:
                json.dump(self.model_info, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving model info: {e}")

    def _download_with_progress(self, url: str, file_path: Path, desc: str) -> bool:
        """Download file with progress bar"""
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                with tqdm(total=total_size, unit='iB', unit_scale=True, desc=desc) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            return True
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            return False

    def _cleanup_files(self, model_path: Optional[Path], download_path: Path, extract_path: Optional[Path] = None):
        """Clean up temporary files"""
        try:
            if download_path.exists():
                download_path.unlink()
            if extract_path and extract_path.exists():
                shutil.rmtree(extract_path, ignore_errors=True)
            if model_path and model_path.exists() and not self._verify_existing_model(model_path.name.split('-')[-1]):
                shutil.rmtree(model_path)
        except Exception as e:
            self.logger.error(f"Error cleaning up files: {e}")

    def get_model_path(self, language: str) -> Optional[Path]:
        """Get path to downloaded model"""
        if self._verify_existing_model(language):
            return self.base_path / f"vosk-model-{language}"
        return None

    def cleanup(self):
        """Clean up all temporary files"""
        try:
            for file in self.base_path.glob("*.zip"):
                file.unlink()
            temp_extract = self.base_path / "temp_extract"
            if temp_extract.exists():
                shutil.rmtree(temp_extract, ignore_errors=True)
        except Exception as e:
            self.logger.error(f"Error cleaning up: {e}")
# core/base.py
from abc import ABC, abstractmethod
import logging
import threading
from typing import Dict, Optional
from datetime import datetime

class BaseModule(ABC):
    """Base class for all system modules"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.running = False
        self._lock = threading.Lock()
        self._initialized = threading.Event()
        self._cleanup_done = False
        
        # Module state
        self._status = {
            'state': 'initializing',
            'last_update': datetime.now().isoformat(),
            'error': None
        }

    @abstractmethod
    def _initialize(self) -> bool:
        """Initialize module - must be implemented by subclasses"""
        pass

    @abstractmethod
    def cleanup(self):
        """Cleanup module resources - must be implemented by subclasses"""
        pass

    def start(self):
        """Start the module"""
        try:
            if self._initialize():
                self.running = True
                self._initialized.set()
                self.update_status('running')
                self.logger.info(f"{self.__class__.__name__} started")
                return True
            else:
                self.update_status('error', "Initialization failed")
                raise RuntimeError(f"{self.__class__.__name__} failed to initialize")
        except Exception as e:
            self.logger.error(f"Error starting {self.__class__.__name__}: {e}")
            self.update_status('error', str(e))
            raise

    def stop(self):
        """Stop the module"""
        if not self._cleanup_done:
            self.running = False
            self._initialized.clear()
            try:
                self.cleanup()
            finally:
                self._cleanup_done = True
            self.update_status('stopped')
            self.logger.info(f"{self.__class__.__name__} stopped")

    def update_status(self, state: str, error: Optional[str] = None):
        """Update module status"""
        with self._lock:
            self._status.update({
                'state': state,
                'last_update': datetime.now().isoformat(),
                'error': error
            })

    def get_status(self) -> Dict:
        """Get current module status"""
        with self._lock:
            return self._status.copy()

    def is_running(self) -> bool:
        """Check if module is running"""
        return bool(self.running and self._initialized.is_set())

    def wait_until_ready(self, timeout: Optional[float] = None) -> bool:
        """Wait until module is initialized"""
        return self._initialized.wait(timeout=timeout)
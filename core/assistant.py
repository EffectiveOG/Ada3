from typing import Dict, Optional
import time
import threading

from core.logger import setup_logging, log_startup, log_shutdown
from core.events import EventBus
from modules.vision.vision_module import VisionModule
from modules.audio.audio_module import AudioModule
from modules.conversation.conversation_module import ConversationModule
from config.config import Config

class Assistant:
    def __init__(self):
        """Initialize the assistant with all its modules"""
        # Initialize logging
        self.logger = setup_logging('Assistant')
        log_startup(self.logger, 'Assistant')
        
        # Initialize core components
        self.config = Config()
        self.event_bus = EventBus()
        
        # Initialize modules
        self.modules: Dict[str, Optional[object]] = {}
        self._init_modules()
        
        # Set up internal state
        self.running = True
        self._shutdown_event = threading.Event()
        
    def _init_modules(self):
        """Initialize all modules with proper error handling"""
        try:
            # Initialize modules in the correct order
            
            # 1. Audio module (needs to be started first for voice input)
            self.logger.info("Initializing Audio Module...")
            self.modules['audio'] = AudioModule(
                config=self.config.audio,
                event_bus=self.event_bus,
                logger=self.logger,
                db_manager=None 
            )
            
            # 2. Conversation module (depends on audio for processing)
            self.logger.info("Initializing Conversation Module...")
            self.modules['conversation'] = ConversationModule(
                config=self.config.conversation,  # Pass the ConversationConfig object directly
                event_bus=self.event_bus,
                logger=self.logger
            )
            
            # 3. Vision module (optional)
            self.logger.info("Initializing Vision Module...")
            self.modules['vision'] = VisionModule(
                config=self.config.vision,
                event_bus=self.event_bus,
                logger=self.logger
            )
            
            self.logger.info("All modules initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize modules: {e}", exc_info=True)
            raise
            
    def start(self):
        """Start the assistant and all its modules"""
        try:
            self.logger.info("Starting assistant modules...")
            
            # Start modules in specific order
            start_order = ['audio', 'conversation', 'vision']
            
            # Start each module
            for module_name in start_order:
                module = self.modules.get(module_name)
                if module:
                    try:
                        log_startup(self.logger, module_name)
                        module.start()
                        # Add a small delay between module starts
                        time.sleep(0.5)
                        # Verify module started successfully
                        if hasattr(module, 'is_running') and not module.is_running():
                            raise RuntimeError(f"{module_name} failed to start properly")
                        self.logger.info(f"{module_name} module started successfully")
                    except Exception as e:
                        self.logger.error(f"Failed to start {module_name} module: {e}", exc_info=True)
                        raise
            
            self.logger.info("Assistant started successfully")
            
            # Main loop
            while self.running and not self._shutdown_event.is_set():
                try:
                    # Check module health
                    self._check_modules()
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}", exc_info=True)
                    
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested")
        finally:
            self.shutdown()
            
    def _check_modules(self):
        """Check the health of all modules"""
        for name, module in self.modules.items():
            if module and hasattr(module, 'is_running'):
                if not module.is_running():
                    self.logger.error(f"Module {name} has stopped unexpectedly")
                    self._shutdown_event.set()
                    break
                # Check module status
                if hasattr(module, 'get_status'):
                    status = module.get_status()
                    if status.get('error'):
                        self.logger.error(f"Module {name} reported error: {status['error']}")
                
    def shutdown(self):
        """Shutdown the assistant and all modules"""
        self.logger.info("Initiating shutdown sequence...")
        self.running = False
        
        # Shutdown modules in reverse order
        shutdown_order = ['vision', 'conversation', 'audio']
        
        for module_name in shutdown_order:
            module = self.modules.get(module_name)
            if module:
                try:
                    log_shutdown(self.logger, module_name)
                    module.stop()
                    self.logger.info(f"{module_name} module stopped successfully")
                except Exception as e:
                    self.logger.error(f"Error stopping {module_name} module: {e}", exc_info=True)
        
        log_shutdown(self.logger, 'Assistant')
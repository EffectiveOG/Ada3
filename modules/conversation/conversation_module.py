from typing import Optional, Dict, List, Any
import time
import queue
import threading
from dataclasses import dataclass, field
from datetime import datetime
import logging

from core.base import BaseModule
from core.events import Event, EventTypes
from .language_processing import LanguageProcessor

@dataclass
class Message:
    """Representation of a conversation message"""
    text: str
    speaker: str  # 'user' or 'assistant'
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConversationModule(BaseModule):
    """Handles conversation flow and context management"""
    
    def __init__(self, config, event_bus, logger=None):
        """Initialize conversation module"""
        super().__init__(logger or logging.getLogger(__name__))
        self.config = config
        self.event_bus = event_bus
        self.processing_thread = None
        self.message_queue = queue.Queue()
        
        # Conversation state
        self.conversation_history = []
        self.current_context = {}
        self.last_activity = time.time()
        self.is_processing = False
        self.context_window = getattr(self.config, 'context_window', 5)

    def _initialize(self) -> bool:
        """Initialize the conversation module components"""
        try:
            # Initialize language processor
            self.language_processor = LanguageProcessor(
                language=getattr(self.config, 'language', 'fr')
            )

            # Subscribe to events
            if self.event_bus:
                self.event_bus.subscribe(EventTypes.VOICE_COMMAND, self.handle_voice_command)
                self.event_bus.subscribe(EventTypes.TEXT_INPUT, self.handle_text_input)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize conversation module: {e}")
            return False

    def start(self):
        """Start the conversation module"""
        if super().start():  # Call parent's start method first
            if self.running:
                self.processing_thread = threading.Thread(
                    target=self._processing_loop,
                    name="ConversationProcessor",
                    daemon=True
                )
                self.processing_thread.start()
                self.logger.info("Conversation module started")
                return True
        return False

    def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=1.0)
                if message is None:  # Shutdown sentinel
                    break
                    
                self.is_processing = True
                self._process_message(message)
                self.is_processing = False
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                self.is_processing = False

    def _process_message(self, message: Message):
        """Process a single message"""
        try:
            # Add message to history
            self.conversation_history.append(message)
            
            # Trim history if needed
            while len(self.conversation_history) > getattr(self.config, 'max_history', 10):
                self.conversation_history.pop(0)
            
            # Process the message using language processor
            processed_text = self.language_processor.process_text(message.text)
            
            # Extract entities
            entities = self.language_processor.extract_entities(processed_text)
            
            # Detect intent
            intent = self.language_processor.detect_intent(processed_text)
            
            # Generate response
            response = self.language_processor.generate_response(
                processed_text,
                self.conversation_history,
                self.current_context
            )
            
            # Publish response if available
            if response:
                self.event_bus.publish(Event(
                    type=EventTypes.SPEECH_OUTPUT,
                    data={
                        'text': response,
                        'language': getattr(self.config, 'language', 'fr')
                    }
                ))
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def handle_voice_command(self, event: Event):
        """Handle incoming voice commands"""
        try:
            command = event.data.get('command')
            if command:
                message = Message(
                    text=command,
                    speaker='user',
                    metadata={'type': 'voice_command'}
                )
                self.message_queue.put(message)
        except Exception as e:
            self.logger.error(f"Error handling voice command: {e}")

    def handle_text_input(self, event: Event):
        """Handle incoming text input"""
        try:
            text = event.data.get('text')
            if text:
                message = Message(
                    text=text,
                    speaker='user',
                    metadata={'type': 'text_input'}
                )
                self.message_queue.put(message)
        except Exception as e:
            self.logger.error(f"Error handling text input: {e}")

    def stop(self):
        """Stop the conversation module"""
        self.running = False
        if self.message_queue:
            self.message_queue.put(None)  # Send shutdown sentinel
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        super().stop()

    def cleanup(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'message_queue'):
                while not self.message_queue.empty():
                    try:
                        self.message_queue.get_nowait()
                    except queue.Empty:
                        break
                        
            self.conversation_history.clear()
            self.current_context.clear()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        finally:
            self.logger.info("Conversation module cleaned up")

    def get_status(self) -> Dict:
        """Get current module status"""
        status = super().get_status()
        status.update({
            'is_processing': self.is_processing,
            'message_queue_size': self.message_queue.qsize() if hasattr(self, 'message_queue') else 0,
            'history_size': len(self.conversation_history),
            'last_activity': self.last_activity
        })
        return status
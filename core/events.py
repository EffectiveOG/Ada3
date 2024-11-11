# core/events.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Callable
from datetime import datetime
import time
import logging
from collections import defaultdict

@dataclass
class Event:
    """Class representing an event in the system"""
    type: str
    data: Any
    timestamp: float = field(default_factory=time.time)

class EventTypes:
    """Constants for event types"""
    VOICE_COMMAND = "voice_command"
    TEXT_INPUT = "text_input"
    SPEECH_OUTPUT = "speech_output"
    SYSTEM_STATUS = "system_status"
    VISION_UPDATE = "vision_update"
    ERROR = "error"
    
    # Add all event types to a set for validation
    ALL_TYPES = {
        VOICE_COMMAND,
        TEXT_INPUT,
        SPEECH_OUTPUT,
        SYSTEM_STATUS,
        VISION_UPDATE,
        ERROR
    }

class EventBus:
    """Central event manager"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.logger = logging.getLogger('EventBus')

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Subscribe a callback function to an event type
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"New subscription for event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """
        Unsubscribe a callback from an event type
        
        Args:
            event_type: Type of event
            callback: Function to unsubscribe
        """
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(callback)
            self.logger.debug(f"Unsubscribed from event: {event_type}")

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event: The event to publish
        """
        self.logger.debug(f"Publishing event: {event.type}")
        for callback in self.subscribers[event.type]:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error processing event {event.type}: {e}")

    def clear_all_subscribers(self):
        """Clear all event subscribers"""
        self.subscribers.clear()
        self.logger.debug("All subscribers cleared")

    def get_subscriber_count(self, event_type: str = None) -> int:
        """
        Get number of subscribers
        
        Args:
            event_type: Optional event type to count subscribers for
            
        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self.subscribers.get(event_type, []))
        return sum(len(subs) for subs in self.subscribers.values())
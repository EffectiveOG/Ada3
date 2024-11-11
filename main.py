import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from core.logger import setup_logging
from core.assistant import Assistant

def main():
    # Initialize logging first
    logger = setup_logging(name='Ada')
    
    try:
        logger.info("Starting Ada Assistant...")
        logger.info("Initializing core components...")
        
        # Initialize and start the assistant
        assistant = Assistant()
        logger.info("Assistant initialized successfully")
        
        # Start the assistant
        assistant.start()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Critical error during startup: {str(e)}", exc_info=True)
    finally:
        logger.info("Assistant shutdown complete")

if __name__ == "__main__":
    main()
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    from modules.conversation.language_processing import LanguageProcessor
    print("Successfully imported LanguageProcessor")
    
    from modules.conversation.conversation_module import ConversationModule
    print("Successfully imported ConversationModule")
    
    from core.assistant import Assistant
    print("Successfully imported Assistant")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("\nPython path:")
    for path in sys.path:
        print(f"  {path}")
    
    print("\nChecking file existence:")
    files_to_check = [
        "modules/conversation/language_processing.py",
        "modules/conversation/conversation_module.py",
        "core/assistant.py"
    ]
    for file in files_to_check:
        path = project_root / file
        print(f"  {file}: {'EXISTS' if path.exists() else 'MISSING'}")
#!/bin/bash

# Confirm before proceeding
read -p "This will delete all files and directories in the current project folder and recreate the structure. Are you sure you want to proceed? (y/n): " confirm
if [[ $confirm != "y" ]]; then
    echo "Operation canceled."
    exit 1
fi

# Get the script's filename to avoid deleting itself
script_name=$(basename "$0")

# Delete all files and directories except the script itself
echo "Deleting all files and directories in the current project folder..."
find . -mindepth 1 -not -name "$script_name" -exec rm -rf {} +

# Create new structure
echo "Creating new project structure..."

# Root files
touch main.py README.md

# Create directories and files
mkdir -p .venv
mkdir -p config core modules/audio modules/vision modules/conversation modules/utils

# Create config files
touch config/config.py

# Create core files
touch core/assistant.py core/events.py core/base.py core/logger.py core/conversation_handler.py

# Create audio module files
touch modules/audio/audio_module.py

# Create vision module files
touch modules/vision/vision_module.py modules/vision/backends.py modules/vision/backend_utils.py

# Create conversation module files
touch modules/conversation/conversation_module.py modules/conversation/language_processing.py

# Create utils files
touch modules/utils/performance.py modules/utils/error_tracker.py

echo "Project structure recreated successfully."
#!/bin/bash

# python3.12和nutika有冲突

echo "Starting build for OTA_Flash_Tool_CLI (Linux)..."

python3 -m nuitka \
    --standalone \
    --onefile \
    --output-dir=output_linux \
    --output-filename=ota_tool_cli \
    --include-package=serial \
    --remove-output \
    --assume-yes-for-downloads \
    --python-flag=-OO \
    OTA_Flash_Tool_CLI.py

if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
    echo "Executable is at: output_linux/ota_tool_cli"
else
    echo "Build failed!"
fi

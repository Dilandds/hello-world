#!/bin/bash

# STL Viewer Run Script
# Activates virtual environment and runs the application

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Set OpenGL environment variables for macOS compatibility
export MESA_GL_VERSION_OVERRIDE=3.3
export VTK_USE_OSMESA=0  # Try hardware rendering first
# Uncomment below if hardware rendering fails:
# export VTK_USE_OSMESA=1  # Force software rendering

# Activate virtual environment and run application
source venv/bin/activate
python main.py

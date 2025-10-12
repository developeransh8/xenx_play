#!/bin/bash

# xenXgon Play Startup Script

echo "================================="
echo "  xenXgon Play Video Server"
echo "================================="
echo ""

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: FFmpeg is not installed or not in PATH"
    echo "Please install FFmpeg first:"
    echo "  - Download from: https://ffmpeg.org/download.html"
    echo "  - Or install via package manager"
    exit 1
fi

echo "✓ FFmpeg found: $(ffmpeg -version | head -1)"
echo ""

# Check if Python dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    echo ""
fi

echo "✓ Python dependencies installed"
echo ""

# Create necessary directories
mkdir -p videos logs
echo "✓ Directories created"
echo ""

# Start the server
echo "Starting xenXgon Play server..."
echo ""
python3 run.py

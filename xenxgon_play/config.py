import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Server configuration
HOST = "0.0.0.0"
PORT = 8000

# Upload settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024 * 1024  # 10GB in bytes
ALLOWED_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.m4v', '.ts', '.m2ts', '.webm'}

# Video codec validation
REQUIRED_VIDEO_CODEC = ['h264', 'avc', 'avc1']

# Audio processing settings
AUDIO_CODEC = 'aac'
AUDIO_BITRATE = '128k'
AUDIO_CHANNELS = '2'
AUDIO_SAMPLE_RATE = '48000'

# HLS settings
HLS_SEGMENT_TIME = 6

# Processing settings
MAX_CONCURRENT_JOBS = 2

# Directories
VIDEO_DIR = BASE_DIR / 'videos'
LOG_DIR = BASE_DIR / 'logs'
DB_PATH = BASE_DIR / 'database.db'

# Create directories if they don't exist
VIDEO_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# Logging configuration
LOG_FILE = LOG_DIR / 'app.log'
FFMPEG_LOG_FILE = LOG_DIR / 'ffmpeg.log'

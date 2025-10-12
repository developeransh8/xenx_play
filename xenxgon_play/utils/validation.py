import logging
from pathlib import Path
import config
from utils.ffmpeg import FFmpegHelper

logger = logging.getLogger(__name__)

class VideoValidator:
    @staticmethod
    def validate_extension(filename):
        """Check if file has allowed extension"""
        ext = Path(filename).suffix.lower()
        return ext in config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_size(file_size):
        """Check if file size is within limits"""
        return 0 < file_size <= config.MAX_UPLOAD_SIZE
    
    @staticmethod
    def validate_video_codec(video_path):
        """Validate that video uses H.264 codec"""
        probe_data = FFmpegHelper.probe_video(video_path)
        
        if not probe_data:
            return False, "Could not analyze video file"
        
        video_codec = FFmpegHelper.get_video_codec(probe_data)
        
        if not video_codec:
            return False, "No video stream found"
        
        if video_codec not in config.REQUIRED_VIDEO_CODEC:
            return False, f"Video codec must be H.264. Found: {video_codec.upper()}. Please convert to H.264 before uploading."
        
        # Check for audio tracks
        video_info = FFmpegHelper.get_video_info(probe_data)
        if not video_info['audio_tracks']:
            return False, "Video must have at least one audio track"
        
        # Check resolution
        width = video_info['width']
        height = video_info['height']
        
        if height < 360:
            return False, "Minimum resolution is 360p"
        
        if height > 4320:
            return False, "Maximum resolution is 4K (3840x2160)"
        
        return True, "Valid H.264 video"
    
    @staticmethod
    def validate_upload(filename, file_size, video_path=None):
        """Complete upload validation"""
        # Check extension
        if not VideoValidator.validate_extension(filename):
            ext = Path(filename).suffix
            return False, f"File type {ext} is not supported. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        if not VideoValidator.validate_file_size(file_size):
            max_size_gb = config.MAX_UPLOAD_SIZE / (1024**3)
            return False, f"File size exceeds maximum limit of {max_size_gb}GB"
        
        # Check video codec if path provided
        if video_path:
            return VideoValidator.validate_video_codec(video_path)
        
        return True, "Initial validation passed"

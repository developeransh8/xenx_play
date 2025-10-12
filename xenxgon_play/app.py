from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import logging
import uuid
import os
from pathlib import Path
from werkzeug.utils import secure_filename
import threading

import config
from database import Database
from utils.validation import VideoValidator
from utils.ffmpeg import FFmpegHelper
import worker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_SIZE
CORS(app)

db = Database()

# Initialize worker queue
processing_queue = worker.ProcessingQueue(db)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    videos = db.get_all_videos()
    return render_template('dashboard.html', videos=videos)

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/watch/<video_id>')
def watch(video_id):
    video = db.get_video(video_id)
    if not video:
        return render_template('error.html', error='Video not found'), 404
    
    audio_tracks = db.get_audio_tracks(video_id)
    return render_template('watch.html', video=video, audio_tracks=audio_tracks)

@app.route('/api/upload', methods=['POST'])
def upload_video():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        original_filename = secure_filename(file.filename)
        
        # Initial validation
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        valid, message = VideoValidator.validate_upload(original_filename, file_size)
        if not valid:
            return jsonify({'success': False, 'error': message}), 400
        
        # Create video record
        video_id = str(uuid.uuid4())
        video_dir = config.VIDEO_DIR / video_id
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_ext = Path(original_filename).suffix
        filename = f'original{file_ext}'
        video_path = video_dir / filename
        file.save(video_path)
        
        # Validate H.264 codec
        valid, message = VideoValidator.validate_video_codec(video_path)
        if not valid:
            # Clean up
            import shutil
            shutil.rmtree(video_dir)
            return jsonify({'success': False, 'error': message}), 400
        
        # Get video metadata
        probe_data = FFmpegHelper.probe_video(video_path)
        video_info = FFmpegHelper.get_video_info(probe_data)
        
        # Create database record
        db.create_video({
            'id': video_id,
            'filename': filename,
            'original_filename': original_filename,
            'status': 'pending',
            'file_size': file_size
        })
        
        # Update with metadata
        db.update_video(video_id, {
            'duration': video_info['duration'],
            'width': video_info['width'],
            'height': video_info['height'],
            'fps': video_info['fps'],
            'video_codec': video_info['video_codec']
        })
        
        # Add to processing queue
        processing_queue.add_job(video_id, str(video_path), video_info)
        
        logger.info(f"Video uploaded successfully: {video_id}")
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'message': 'Video uploaded successfully and queued for processing'
        })
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos', methods=['GET'])
def get_videos():
    try:
        videos = db.get_all_videos()
        
        # Add audio track count
        for video in videos:
            audio_tracks = db.get_audio_tracks(video['id'])
            video['audio_track_count'] = len(audio_tracks)
        
        return jsonify({'success': True, 'videos': videos})
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    try:
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        audio_tracks = db.get_audio_tracks(video_id)
        video['audio_tracks'] = audio_tracks
        
        return jsonify({'success': True, 'video': video})
    except Exception as e:
        logger.error(f"Error fetching video: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/<video_id>/status', methods=['GET'])
def get_video_status(video_id):
    try:
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        return jsonify({
            'success': True,
            'status': video['status'],
            'progress': video['progress'],
            'error_message': video.get('error_message')
        })
    except Exception as e:
        logger.error(f"Error fetching status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/<video_id>/watch', methods=['POST'])
def increment_watch(video_id):
    try:
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        db.increment_watch_count(video_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error incrementing watch count: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/videos/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    try:
        video = db.get_video(video_id)
        if not video:
            return jsonify({'success': False, 'error': 'Video not found'}), 404
        
        # Delete from database
        db.delete_video(video_id)
        
        # Delete files
        video_dir = config.VIDEO_DIR / video_id
        if video_dir.exists():
            import shutil
            shutil.rmtree(video_dir)
        
        logger.info(f"Video deleted: {video_id}")
        return jsonify({'success': True, 'message': 'Video deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/videos/<video_id>/<path:filename>')
def serve_video_file(video_id, filename):
    """Serve HLS playlist and segment files"""
    video_dir = config.VIDEO_DIR / video_id
    return send_from_directory(video_dir, filename)

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=True)

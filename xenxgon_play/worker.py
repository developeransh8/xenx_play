import threading
import queue
import logging
import time
from pathlib import Path
import config
from utils.ffmpeg import FFmpegHelper

logger = logging.getLogger(__name__)

class ProcessingQueue:
    def __init__(self, database):
        self.db = database
        self.job_queue = queue.Queue()
        self.active_jobs = 0
        self.max_concurrent = config.MAX_CONCURRENT_JOBS
        self.lock = threading.Lock()
        
        # Start worker threads
        for i in range(self.max_concurrent):
            thread = threading.Thread(target=self.worker, daemon=True)
            thread.start()
            logger.info(f"Started worker thread {i+1}")
    
    def add_job(self, video_id, video_path, video_info):
        """Add video processing job to queue"""
        job = {
            'video_id': video_id,
            'video_path': video_path,
            'video_info': video_info
        }
        self.job_queue.put(job)
        logger.info(f"Added job to queue: {video_id}")
    
    def worker(self):
        """Worker thread that processes videos"""
        while True:
            try:
                job = self.job_queue.get()
                
                with self.lock:
                    self.active_jobs += 1
                
                logger.info(f"Processing job: {job['video_id']}")
                self.process_video(job)
                
                with self.lock:
                    self.active_jobs -= 1
                
                self.job_queue.task_done()
            except Exception as e:
                logger.error(f"Worker error: {e}")
                with self.lock:
                    self.active_jobs -= 1
    
    def process_video(self, job):
        """Process video: extract video stream and audio tracks"""
        video_id = job['video_id']
        video_path = Path(job['video_path'])
        video_info = job['video_info']
        output_dir = video_path.parent
        
        try:
            # Update status
            self.db.update_video(video_id, {
                'status': 'processing',
                'progress': 0
            })
            
            # Step 1: Extract video-only stream (10% progress)
            logger.info(f"Extracting video stream for {video_id}")
            self.db.update_video(video_id, {'progress': 5})
            
            success = FFmpegHelper.extract_video_only(
                video_path,
                output_dir,
                lambda line: self.parse_progress(video_id, line, 5, 15)
            )
            
            if not success:
                raise Exception("Failed to extract video stream")
            
            self.db.update_video(video_id, {'progress': 15})
            
            # Step 2: Process audio tracks
            audio_tracks = video_info.get('audio_tracks', [])
            total_tracks = len(audio_tracks)
            
            if total_tracks == 0:
                raise Exception("No audio tracks found")
            
            logger.info(f"Processing {total_tracks} audio tracks for {video_id}")
            
            progress_per_track = 70 / total_tracks  # 70% for audio processing
            base_progress = 15
            
            for i, track_info in enumerate(audio_tracks):
                track_index = track_info['index']
                logger.info(f"Processing audio track {track_index}")
                
                success = FFmpegHelper.extract_audio_track(
                    video_path,
                    output_dir,
                    track_index,
                    lambda line: self.parse_progress(
                        video_id,
                        line,
                        base_progress + int(i * progress_per_track),
                        base_progress + int((i + 1) * progress_per_track)
                    )
                )
                
                if not success:
                    logger.warning(f"Failed to extract audio track {track_index}")
                    continue
                
                # Save audio track info to database
                self.db.create_audio_track({
                    'video_id': video_id,
                    'track_index': track_index,
                    'language': track_info.get('language', 'und'),
                    'title': track_info.get('title', f"Audio Track {track_index}"),
                    'codec': 'aac',
                    'channels': 2,
                    'sample_rate': 48000,
                    'is_default': i == 0,  # First track is default
                    'hls_playlist_path': f'audio_track_{track_index}.m3u8'
                })
            
            self.db.update_video(video_id, {'progress': 85})
            
            # Step 3: Generate master playlist
            logger.info(f"Generating master playlist for {video_id}")
            audio_tracks_db = self.db.get_audio_tracks(video_id)
            
            success = FFmpegHelper.generate_master_playlist(output_dir, audio_tracks_db)
            if not success:
                raise Exception("Failed to generate master playlist")
            
            self.db.update_video(video_id, {'progress': 90})
            
            # Step 4: Generate thumbnail
            logger.info(f"Generating thumbnail for {video_id}")
            thumbnail_path = output_dir / 'thumb.jpg'
            
            # Calculate 10% timestamp
            duration = video_info.get('duration', 0)
            timestamp_seconds = int(duration * 0.1)
            hours = timestamp_seconds // 3600
            minutes = (timestamp_seconds % 3600) // 60
            seconds = timestamp_seconds % 60
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            FFmpegHelper.generate_thumbnail(video_path, thumbnail_path, timestamp)
            
            self.db.update_video(video_id, {'progress': 95})
            
            # Step 5: Update final status
            self.db.update_video(video_id, {
                'status': 'ready',
                'progress': 100,
                'hls_master_path': 'playlist_master.m3u8',
                'thumbnail_path': 'thumb.jpg',
                'processed_at': 'CURRENT_TIMESTAMP'
            })
            
            logger.info(f"Video processing completed: {video_id}")
        
        except Exception as e:
            logger.error(f"Processing error for {video_id}: {e}")
            self.db.update_video(video_id, {
                'status': 'failed',
                'error_message': str(e)
            })
    
    def parse_progress(self, video_id, line, min_progress, max_progress):
        """Parse FFmpeg output for progress updates"""
        # This is a simple progress parser
        # In production, you'd parse FFmpeg's time output
        pass

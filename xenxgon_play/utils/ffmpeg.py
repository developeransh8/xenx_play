import subprocess
import json
import logging
from pathlib import Path
import config

logger = logging.getLogger(__name__)

class FFmpegHelper:
    @staticmethod
    def probe_video(video_path):
        """Extract video metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"FFprobe error: {result.stderr}")
                return None
            
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Error probing video: {e}")
            return None
    
    @staticmethod
    def get_video_codec(probe_data):
        """Extract video codec from probe data"""
        if not probe_data or 'streams' not in probe_data:
            return None
        
        for stream in probe_data['streams']:
            if stream.get('codec_type') == 'video':
                codec_name = stream.get('codec_name', '').lower()
                return codec_name
        return None
    
    @staticmethod
    def get_video_info(probe_data):
        """Extract video information"""
        info = {
            'duration': 0,
            'width': 0,
            'height': 0,
            'fps': 0,
            'video_codec': '',
            'audio_tracks': []
        }
        
        if not probe_data:
            return info
        
        # Get format duration
        if 'format' in probe_data:
            info['duration'] = float(probe_data['format'].get('duration', 0))
        
        # Process streams
        audio_track_index = 0
        for stream in probe_data.get('streams', []):
            if stream.get('codec_type') == 'video':
                info['width'] = stream.get('width', 0)
                info['height'] = stream.get('height', 0)
                info['video_codec'] = stream.get('codec_name', '')
                
                # Calculate FPS
                fps_str = stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    num, den = fps_str.split('/')
                    if int(den) != 0:
                        info['fps'] = int(num) / int(den)
            
            elif stream.get('codec_type') == 'audio':
                tags = stream.get('tags', {})
                info['audio_tracks'].append({
                    'index': audio_track_index,
                    'codec': stream.get('codec_name', ''),
                    'channels': stream.get('channels', 2),
                    'sample_rate': stream.get('sample_rate', 48000),
                    'language': tags.get('language', 'und'),
                    'title': tags.get('title', f'Audio Track {audio_track_index}')
                })
                audio_track_index += 1
        
        return info
    
    @staticmethod
    def extract_video_only(input_path, output_dir, progress_callback=None):
        """Extract video-only HLS stream"""
        output_dir = Path(output_dir)
        playlist_path = output_dir / 'video_only.m3u8'
        segment_pattern = str(output_dir / 'video_segment_%03d.ts')
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-map', '0:v:0',
            '-c:v', 'copy',
            '-an',
            '-f', 'hls',
            '-hls_time', str(config.HLS_SEGMENT_TIME),
            '-hls_list_size', '0',
            '-hls_segment_filename', segment_pattern,
            str(playlist_path)
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            for line in process.stderr:
                if progress_callback:
                    progress_callback(line)
            
            process.wait()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg video extraction failed")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error extracting video: {e}")
            return False
    
    @staticmethod
    def extract_audio_track(input_path, output_dir, track_index, progress_callback=None):
        """Extract and convert audio track to AAC HLS"""
        output_dir = Path(output_dir)
        playlist_path = output_dir / f'audio_track_{track_index}.m3u8'
        segment_pattern = str(output_dir / f'audio_{track_index}_segment_%03d.ts')
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-map', f'0:a:{track_index}',
            '-c:a', config.AUDIO_CODEC,
            '-b:a', config.AUDIO_BITRATE,
            '-ac', config.AUDIO_CHANNELS,
            '-ar', config.AUDIO_SAMPLE_RATE,
            '-profile:a', 'aac_low',
            '-f', 'hls',
            '-hls_time', str(config.HLS_SEGMENT_TIME),
            '-hls_list_size', '0',
            '-hls_segment_filename', segment_pattern,
            str(playlist_path)
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            for line in process.stderr:
                if progress_callback:
                    progress_callback(line)
            
            process.wait()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg audio extraction failed for track {track_index}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error extracting audio track {track_index}: {e}")
            return False
    
    @staticmethod
    def generate_thumbnail(input_path, output_path, timestamp='00:00:10'):
        """Generate video thumbnail"""
        cmd = [
            'ffmpeg',
            '-ss', timestamp,
            '-i', str(input_path),
            '-vframes', '1',
            '-q:v', '2',
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return False
    
    @staticmethod
    def generate_master_playlist(output_dir, audio_tracks):
        """Generate master HLS playlist with audio variants"""
        output_dir = Path(output_dir)
        master_path = output_dir / 'playlist_master.m3u8'
        
        lines = [
            '#EXTM3U',
            '#EXT-X-VERSION:3',
            '#EXT-X-INDEPENDENT-SEGMENTS'
        ]
        
        # Add audio variants
        for track in audio_tracks:
            default = 'YES' if track.get('is_default') else 'NO'
            autoselect = 'YES' if track.get('is_default') else 'YES'
            language = track.get('language', 'und')
            name = track.get('title', f"Audio Track {track.get('track_index', 0)}")
            uri = f"audio_track_{track.get('track_index', 0)}.m3u8"
            
            lines.append(
                f'#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",LANGUAGE="{language}",'
                f'NAME="{name}",DEFAULT={default},AUTOSELECT={autoselect},URI="{uri}"'
            )
        
        # Add video stream
        lines.append('#EXT-X-STREAM-INF:BANDWIDTH=4000000,CODECS="avc1.640029,mp4a.40.2",AUDIO="audio"')
        lines.append('video_only.m3u8')
        
        try:
            with open(master_path, 'w') as f:
                f.write('\n'.join(lines))
            return True
        except Exception as e:
            logger.error(f"Error generating master playlist: {e}")
            return False

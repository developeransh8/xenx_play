# xenXgon Play - Video Streaming Server

A Windows 11 video streaming server that processes H.264 videos with multi-audio track support and streams via HLS to all devices including TV browsers.

## Features

✅ **H.264 Only** - Strict validation, rejects non-H.264 videos
✅ **No Video Re-encoding** - Fast processing (5-10 minutes per video)
✅ **Multi-Audio Tracks** - Detects and converts all audio tracks to AAC
✅ **HLS Streaming** - Adaptive streaming with master playlists
✅ **Universal Compatibility** - Works on TV browsers, desktop, and mobile
✅ **Audio Track Switching** - Seamless audio switching during playback
✅ **TV Optimized UI** - Large buttons, clear focus, D-pad navigation

## Requirements

- Python 3.10+
- FFmpeg 6.0+ (must be in PATH)
- Windows 11

## Installation

### 1. Install FFmpeg

Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

Add FFmpeg to your system PATH:
1. Extract FFmpeg to `C:\ffmpeg`
2. Add `C:\ffmpeg\bin` to your PATH environment variable
3. Verify installation: `ffmpeg -version`

### 2. Install Python Dependencies

```bash
cd xenxgon_play
pip install -r requirements.txt
```

### 3. Create Environment File (Optional)

```bash
cp .env.example .env
```

Edit `.env` if you want to customize settings.

## Usage

### Start the Server

```bash
python run.py
```

Server will start at: `http://localhost:8000`

### Upload Videos

1. Navigate to Upload page
2. Drag & drop or click to browse
3. Select H.264 encoded video (MP4, MKV, MOV, etc.)
4. Wait for upload and processing
5. Video will appear in Dashboard when ready

### Watch Videos

1. Click "Watch" on any video in Dashboard
2. Video plays with HLS streaming
3. If multiple audio tracks available, use audio selector button
4. Switch between audio tracks during playback

## Project Structure

```
xenxgon_play/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── database.py            # SQLite operations
├── worker.py              # Background video processing
├── run.py                 # Waitress production server
├── requirements.txt       # Python dependencies
├── utils/
│   ├── ffmpeg.py          # FFmpeg utilities
│   └── validation.py      # Upload validation
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── watch.html
│   └── error.html
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── tv-optimized.css
│   └── js/
│       ├── app.js
│       ├── upload.js
│       └── player.js
├── videos/                # Video storage
├── logs/                  # Application logs
└── database.db            # SQLite database
```

## How It Works

### Upload & Validation

1. User uploads video file
2. Server validates file extension and size
3. FFprobe checks video codec (must be H.264)
4. If not H.264, upload is rejected with error message
5. Video metadata extracted (duration, resolution, audio tracks)
6. Video saved to `videos/{uuid}/` directory

### Processing Workflow

1. **Extract Video Stream** - Copy H.264 video to HLS segments (no re-encoding)
2. **Process Audio Tracks** - Convert each audio track to AAC stereo 48kHz 128kbps
3. **Generate Playlists** - Create individual HLS playlists for each audio track
4. **Master Playlist** - Generate master playlist with all audio variants
5. **Thumbnail** - Extract thumbnail at 10% timestamp
6. **Database Update** - Mark video as ready

### HLS Structure

Each processed video has:

```
videos/{uuid}/
├── original.mp4              # Original uploaded file
├── playlist_master.m3u8      # Master playlist
├── video_only.m3u8           # Video-only stream
├── audio_track_0.m3u8        # First audio track
├── audio_track_1.m3u8        # Second audio track (if exists)
├── video_segment_000.ts      # Video segments
├── video_segment_001.ts
├── audio_0_segment_000.ts    # Audio track 0 segments
├── audio_1_segment_000.ts    # Audio track 1 segments
└── thumb.jpg                 # Thumbnail
```

## API Endpoints

### Pages

- `GET /` - Redirect to dashboard
- `GET /dashboard` - Video library
- `GET /upload` - Upload interface
- `GET /watch/<video_id>` - Video player

### API

- `POST /api/upload` - Upload video file
- `GET /api/videos` - List all videos
- `GET /api/videos/<video_id>` - Get video details
- `GET /api/videos/<video_id>/status` - Get processing status
- `POST /api/videos/<video_id>/watch` - Increment watch count
- `DELETE /api/videos/<video_id>` - Delete video
- `GET /videos/<video_id>/<filename>` - Serve HLS files

## Configuration

Edit `config.py` to customize:

- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)
- `MAX_UPLOAD_SIZE` - Maximum file size (default: 10GB)
- `HLS_SEGMENT_TIME` - Segment duration (default: 6 seconds)
- `MAX_CONCURRENT_JOBS` - Concurrent processing jobs (default: 2)
- `AUDIO_BITRATE` - Audio bitrate (default: 128k)

## TV Browser Optimization

### Tested On

- LG webOS TV
- Samsung Tizen TV
- Sony Bravia
- Chrome Desktop
- Firefox Desktop
- Safari Desktop
- iOS Safari
- Android Chrome

### Optimizations

- Large text (24px+) for TV readability
- Large buttons (48px+ touch targets)
- Clear focus indicators (3px borders)
- D-pad navigation support
- No hover-dependent interactions
- Keyboard shortcuts for video control

### Keyboard Controls

- `Space` / `K` - Play/Pause
- `F` - Fullscreen
- `M` - Mute/Unmute
- `←` / `→` - Seek backward/forward 5 seconds
- `↑` / `↓` - Volume up/down (when not in audio menu)
- `Enter` - Select focused element
- `Esc` - Close audio menu

## Troubleshooting

### FFmpeg Not Found

```
Error: FFmpeg not found in PATH
```

**Solution:** Install FFmpeg and add to PATH (see Installation section)

### Video Rejected

```
Error: Video codec must be H.264. Found: H265.
```

**Solution:** Convert video to H.264 before uploading:

```bash
ffmpeg -i input.mp4 -c:v libx264 -c:a copy output.mp4
```

### Processing Failed

```
Status: failed
```

**Solution:** Check logs in `logs/ffmpeg.log` for details

### No Audio Tracks

```
Error: Video must have at least one audio track
```

**Solution:** Ensure video has audio stream

## Performance

### Processing Speed

- **H.264 video**: 5-10 minutes per video (audio-only processing)
- **Non-H.264**: Rejected (no processing)

### Why So Fast?

- Video stream is COPIED (not re-encoded)
- Only audio streams are converted
- Parallel processing of audio tracks
- Background worker queue

## Database Schema

### Videos Table

- `id` - UUID primary key
- `filename` - Storage filename
- `original_filename` - User's filename
- `status` - uploading, pending, processing, ready, failed
- `progress` - 0-100%
- `duration`, `width`, `height`, `fps` - Video metadata
- `video_codec` - Should always be h264
- `file_size` - Bytes
- `hls_master_path` - Master playlist path
- `thumbnail_path` - Thumbnail image path
- `error_message` - Error if failed
- `created_at`, `processed_at` - Timestamps
- `watch_count` - View counter

### Audio Tracks Table

- `id` - Auto increment
- `video_id` - Foreign key to videos
- `track_index` - 0, 1, 2, etc.
- `language` - Language code (eng, spa, etc.)
- `title` - Track name
- `codec` - Always aac
- `channels` - Always 2 (stereo)
- `sample_rate` - Always 48000
- `is_default` - First track is default
- `hls_playlist_path` - Playlist filename

## Development

### Debug Mode

```bash
python app.py
```

Runs Flask development server with debug mode.

### Production Mode

```bash
python run.py
```

Runs Waitress WSGI server for production.

## License

MIT License

## Support

For issues or questions, please create an issue on GitHub.

# xenXgon Play - Quick Start Guide

## Installation (5 Minutes)

### 1. Install FFmpeg

**Windows 11:**
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH
4. Open new terminal and verify: `ffmpeg -version`

**Linux:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### 2. Install Python Dependencies

```bash
cd xenxgon_play
pip install -r requirements.txt
```

### 3. Start Server

```bash
python run.py
```

Or use the startup script:
```bash
./start.sh
```

Server will be available at: **http://localhost:8000**

## Usage

### Upload Video

1. Go to **http://localhost:8000/upload**
2. Drag & drop your H.264 video (or click to browse)
3. Wait for upload to complete
4. Video will be processed automatically (5-10 minutes)

### Watch Video

1. Go to **http://localhost:8000/dashboard**
2. Click "Watch" on any ready video
3. Video plays with HLS streaming
4. If multiple audio tracks exist, click audio button to switch

## Important Notes

### ✅ Accepted Videos

- **Video codec**: H.264 (AVC) only
- **Formats**: MP4, MKV, MOV, M4V, TS, M2TS, WebM (with H.264 video)
- **Resolution**: 360p minimum, 4K maximum
- **File size**: Up to 10GB
- **Audio**: At least one audio track required

### ❌ Rejected Videos

Videos with non-H.264 codecs (H.265/HEVC, VP8, VP9, etc.) will be rejected with error:

```
"Video codec must be H.264. Found: [codec]. Please convert to H.264 before uploading."
```

### Convert Non-H.264 Video

```bash
ffmpeg -i input.mp4 -c:v libx264 -c:a copy output.mp4
```

## Why H.264 Only?

**Speed:** Video is copied (not re-encoded), processing is 3-4x faster

- With re-encoding: 15-20 minutes per video
- Without re-encoding: 5-10 minutes per video

Only audio tracks are converted to AAC for HLS compatibility.

## Features

- ✅ **Fast Processing** - 5-10 minutes per video
- ✅ **Multi-Audio** - Detects and processes all audio tracks
- ✅ **HLS Streaming** - Works on all devices (TV, desktop, mobile)
- ✅ **Audio Switching** - Change audio track during playback
- ✅ **TV Optimized** - Large buttons, clear focus, D-pad navigation
- ✅ **Real-time Progress** - Watch processing status live
- ✅ **Auto Thumbnails** - Generated at 10% timestamp

## Keyboard Shortcuts (Video Player)

- `Space` / `K` - Play/Pause
- `F` - Fullscreen
- `M` - Mute/Unmute
- `←` / `→` - Seek -5s / +5s
- `↑` / `↓` - Volume up/down
- `Enter` - Select focused element
- `Esc` - Close menus

## File Structure

Each processed video creates:

```
videos/{uuid}/
├── original.mp4              # Your uploaded file
├── playlist_master.m3u8      # Master HLS playlist
├── video_only.m3u8           # Video stream
├── audio_track_0.m3u8        # Audio track 1
├── audio_track_1.m3u8        # Audio track 2 (if exists)
├── video_segment_*.ts        # Video segments (6 seconds each)
├── audio_*_segment_*.ts      # Audio segments
└── thumb.jpg                 # Thumbnail
```

## Troubleshooting

### "FFmpeg not found"

Make sure FFmpeg is installed and in your PATH:
```bash
ffmpeg -version
```

### "Video codec must be H.264"

Your video uses a different codec. Convert it:
```bash
ffmpeg -i input.mp4 -c:v libx264 -preset medium -crf 23 -c:a copy output.mp4
```

### Processing stuck at 0%

Check logs:
```bash
tail -f logs/app.log
tail -f logs/ffmpeg.log
```

### Server not starting

Check if port 8000 is available:
```bash
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

## API Quick Reference

### Upload Video
```bash
curl -X POST -F "file=@video.mp4" http://localhost:8000/api/upload
```

### List Videos
```bash
curl http://localhost:8000/api/videos
```

### Get Video Details
```bash
curl http://localhost:8000/api/videos/{video_id}
```

### Check Processing Status
```bash
curl http://localhost:8000/api/videos/{video_id}/status
```

### Delete Video
```bash
curl -X DELETE http://localhost:8000/api/videos/{video_id}
```

## Production Deployment

For production use:

1. Use a reverse proxy (nginx/Apache) with HTTPS
2. Configure firewall rules
3. Set up automated backups
4. Monitor disk space (videos directory grows quickly)
5. Enable log rotation
6. Consider using cloud storage (S3/Azure/GCS)

## Support

For issues or questions:
- Check logs in `logs/` directory
- Read full documentation in `README.md`
- See test results in `TESTING.md`

## System Requirements

- **OS**: Windows 11 (primary), Linux (tested), macOS (should work)
- **Python**: 3.10+
- **FFmpeg**: 6.0+ (5.1+ works)
- **Disk Space**: Depends on video count (each video ~2-3x original size)
- **RAM**: 2GB minimum, 4GB+ recommended
- **CPU**: Multi-core recommended for concurrent processing

## What's Next?

After getting familiar with the basics:

1. Test multi-audio track videos
2. Try uploading different H.264 formats (MKV, MOV, etc.)
3. Test on TV browser if available
4. Experiment with keyboard navigation
5. Check the API for integration possibilities

Enjoy streaming! 🎬

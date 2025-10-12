# xenXgon Play - System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        xenXgon Play                              │
│                   Video Streaming Server                         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                            USER LAYER                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │   TV     │  │ Desktop  │  │  Mobile  │  │  Tablet  │           │
│  │ Browser  │  │ Browser  │  │ Browser  │  │ Browser  │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │              │              │                  │
│       └─────────────┴──────────────┴──────────────┘                 │
│                            │                                          │
│                        HTTP/HTTPS                                    │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       WEB SERVER LAYER                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Waitress WSGI Server                       │   │
│  │                    (Port 8000)                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                             │                                         │
│                             ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Flask Application                          │   │
│  │                    (app.py)                                   │   │
│  │                                                               │   │
│  │  Routes:                                                      │   │
│  │  • /                    → Dashboard                           │   │
│  │  • /dashboard           → Video list                          │   │
│  │  • /upload              → Upload page                         │   │
│  │  • /watch/<id>          → Video player                        │   │
│  │  • /api/upload          → Upload API                          │   │
│  │  • /api/videos          → List videos                         │   │
│  │  • /api/videos/<id>     → Video details                       │   │
│  │  • /videos/<id>/<file>  → Serve HLS files                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                             │                                         │
└─────────────────────────────┼─────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   VALIDATION     │ │   DATABASE       │ │   PROCESSING     │
│     LAYER        │ │     LAYER        │ │     LAYER        │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│                  │ │                  │ │                  │
│ ┌──────────────┐ │ │ ┌──────────────┐ │ │ ┌──────────────┐ │
│ │ validation.py│ │ │ │ database.py  │ │ │ │  worker.py   │ │
│ │              │ │ │ │              │ │ │ │              │ │
│ │ • Extension  │ │ │ │ SQLite DB    │ │ │ │ Background   │ │
│ │ • File size  │ │ │ │              │ │ │ │ Worker Queue │ │
│ │ • H.264 check│ │ │ │ Tables:      │ │ │ │              │ │
│ │ • FFprobe    │ │ │ │ • videos     │ │ │ │ Max 2        │ │
│ │              │ │ │ │ • audio_trks │ │ │ │ concurrent   │ │
│ └──────────────┘ │ │ │              │ │ │ │ jobs         │ │
│                  │ │ └──────────────┘ │ │ └──────┬───────┘ │
└──────────────────┘ └──────────────────┘ └────────┼─────────┘
                                                    │
                                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       FFMPEG LAYER                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ffmpeg.py (Utils)                          │   │
│  │                                                               │   │
│  │  Functions:                                                   │   │
│  │  • probe_video()          → Extract metadata                 │   │
│  │  • extract_video_only()   → Copy H.264 stream                │   │
│  │  • extract_audio_track()  → Convert audio to AAC             │   │
│  │  • generate_thumbnail()   → Create thumbnail                 │   │
│  │  • generate_master_playlist() → Create HLS master            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                             │                                         │
│                             ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    FFmpeg Binary                              │   │
│  │                    (External)                                 │   │
│  │                                                               │   │
│  │  Commands:                                                    │   │
│  │  • ffprobe    → Analyze video                                │   │
│  │  • ffmpeg     → Process video/audio                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                             │                                         │
└─────────────────────────────┼─────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  videos/                                                              │
│  └── {uuid}/                                                          │
│      ├── original.mp4              ← Original upload                 │
│      ├── playlist_master.m3u8      ← Master HLS playlist             │
│      ├── video_only.m3u8           ← Video stream playlist           │
│      ├── audio_track_0.m3u8        ← Audio track 0 playlist          │
│      ├── audio_track_1.m3u8        ← Audio track 1 playlist          │
│      ├── video_segment_*.ts        ← Video segments (H.264 copied)   │
│      ├── audio_*_segment_*.ts      ← Audio segments (AAC converted)  │
│      └── thumb.jpg                 ← Thumbnail                       │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### Upload & Processing Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Upload video
     ▼
┌─────────────────┐
│  Upload Page    │
│  (upload.html)  │
└────┬────────────┘
     │ 2. POST /api/upload
     ▼
┌─────────────────────────────────────────────────────┐
│              Flask Upload Handler                    │
│                                                      │
│  Step 1: Validate extension & size                  │
│  Step 2: Save temporary file                        │
│  Step 3: Run FFprobe to check codec                 │
│  Step 4: If not H.264 → REJECT                      │
│  Step 5: If H.264 → Accept                          │
│  Step 6: Move to videos/{uuid}/ directory           │
│  Step 7: Extract metadata (duration, tracks, etc.)  │
│  Step 8: Create database record                     │
│  Step 9: Add to processing queue                    │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│           Background Worker Thread                   │
│                                                      │
│  Step 1: Extract video-only HLS (copy H.264)        │
│         ├─ video_only.m3u8                          │
│         └─ video_segment_*.ts                       │
│                                                      │
│  Step 2: For each audio track:                      │
│         ├─ Convert to AAC 128k stereo 48kHz         │
│         ├─ Generate audio_track_N.m3u8              │
│         ├─ Create audio_N_segment_*.ts              │
│         └─ Save track info to database              │
│                                                      │
│  Step 3: Generate master playlist                   │
│         └─ playlist_master.m3u8                     │
│                                                      │
│  Step 4: Generate thumbnail                         │
│         └─ thumb.jpg                                │
│                                                      │
│  Step 5: Update status to 'ready'                   │
└─────────────────────────────────────────────────────┘
```

### Playback Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Click "Watch"
     ▼
┌─────────────────┐
│  Watch Page     │
│  (watch.html)   │
└────┬────────────┘
     │ 2. Load Video.js player
     ▼
┌──────────────────────────────────────────┐
│        Video.js Player                    │
│                                           │
│  Source: /videos/{uuid}/playlist_master.m3u8
└────┬──────────────────────────────────────┘
     │ 3. Request master playlist
     ▼
┌──────────────────────────────────────────┐
│      Flask File Server                    │
│  GET /videos/{uuid}/playlist_master.m3u8 │
└────┬──────────────────────────────────────┘
     │ 4. Parse playlist
     ▼
┌──────────────────────────────────────────┐
│      Master Playlist                      │
│                                           │
│  #EXT-X-MEDIA: audio_track_0.m3u8        │
│  #EXT-X-MEDIA: audio_track_1.m3u8        │
│  #EXT-X-STREAM-INF: video_only.m3u8      │
└────┬──────────────────────────────────────┘
     │ 5. Request streams
     ├──────────────┬──────────────┐
     ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────┐
│ Video   │  │ Audio    │  │ Audio    │
│ Stream  │  │ Track 0  │  │ Track 1  │
│ (H.264) │  │ (AAC)    │  │ (AAC)    │
└─────────┘  └──────────┘  └──────────┘
     │              │              │
     │ 6. Download segments        │
     ├──────────────┴──────────────┘
     ▼
┌──────────────────────────────────────────┐
│         Video.js Player                   │
│                                           │
│  • Plays video segments                  │
│  • Mixes selected audio track            │
│  • Handles audio switching                │
│  • Shows controls                         │
└──────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────┐
│      User watches video with              │
│      ability to switch audio tracks       │
└──────────────────────────────────────────┘
```

### Audio Track Switching Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1. Click audio button
     ▼
┌──────────────────────────────────────────┐
│      Audio Selector Menu                  │
│                                           │
│  ○ Audio Track 0 (English) [Default]     │
│  ○ Audio Track 1 (Spanish)                │
└────┬──────────────────────────────────────┘
     │ 2. Select different track
     ▼
┌──────────────────────────────────────────┐
│      player.js (JavaScript)               │
│                                           │
│  1. Save current playback position        │
│  2. Switch audio source                   │
│  3. Reload player with new audio          │
│  4. Resume at saved position              │
│  5. Save preference to localStorage       │
└──────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────┐
│      Video continues playing with         │
│      new audio track seamlessly           │
└──────────────────────────────────────────┘
```

## Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│                         videos                               │
├─────────────────────────────────────────────────────────────┤
│ id                 TEXT PRIMARY KEY                          │
│ filename           TEXT                                      │
│ original_filename  TEXT                                      │
│ status             TEXT (uploading/pending/processing/       │
│                         ready/failed)                        │
│ progress           INTEGER (0-100)                           │
│ duration           REAL                                      │
│ width              INTEGER                                   │
│ height             INTEGER                                   │
│ fps                REAL                                      │
│ video_codec        TEXT (h264)                               │
│ file_size          INTEGER                                   │
│ hls_master_path    TEXT                                      │
│ thumbnail_path     TEXT                                      │
│ error_message      TEXT                                      │
│ created_at         TIMESTAMP                                 │
│ processed_at       TIMESTAMP                                 │
│ watch_count        INTEGER                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      audio_tracks                            │
├─────────────────────────────────────────────────────────────┤
│ id                 INTEGER PRIMARY KEY                       │
│ video_id           TEXT FOREIGN KEY → videos.id             │
│ track_index        INTEGER (0, 1, 2, ...)                   │
│ language           TEXT (eng, spa, und, ...)                │
│ title              TEXT                                      │
│ codec              TEXT (aac)                                │
│ channels           INTEGER (2)                               │
│ sample_rate        INTEGER (48000)                           │
│ is_default         BOOLEAN                                   │
│ hls_playlist_path  TEXT                                      │
└─────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      templates/                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  base.html                                                    │
│  ├─ Navbar                                                    │
│  ├─ Video.js CDN                                             │
│  ├─ Custom CSS                                               │
│  └─ Block content                                            │
│                                                               │
│  dashboard.html (extends base)                               │
│  ├─ Video grid                                               │
│  ├─ Video cards                                              │
│  ├─ Status badges                                            │
│  ├─ Progress bars                                            │
│  └─ Delete modal                                             │
│                                                               │
│  upload.html (extends base)                                  │
│  ├─ Drag & drop zone                                         │
│  ├─ Progress indicator                                       │
│  └─ Requirements list                                        │
│                                                               │
│  watch.html (extends base)                                   │
│  ├─ Video.js player                                          │
│  ├─ Audio selector overlay                                   │
│  └─ Video details                                            │
│                                                               │
│  error.html (extends base)                                   │
│  └─ Error message                                            │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       static/                                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  css/                                                         │
│  ├─ style.css                                                │
│  │  ├─ Modern design                                         │
│  │  ├─ Responsive layout                                     │
│  │  └─ Component styles                                      │
│  └─ tv-optimized.css                                         │
│     ├─ Large text (24px+)                                    │
│     ├─ Large buttons (48px+)                                 │
│     ├─ Clear focus (3px)                                     │
│     └─ D-pad navigation                                      │
│                                                               │
│  js/                                                          │
│  ├─ app.js                                                   │
│  │  ├─ Keyboard navigation                                   │
│  │  └─ Utility functions                                     │
│  ├─ upload.js                                                │
│  │  ├─ Drag & drop                                           │
│  │  ├─ File validation                                       │
│  │  └─ Upload progress                                       │
│  └─ player.js                                                │
│     ├─ Video.js init                                         │
│     ├─ Audio switching                                       │
│     ├─ Keyboard shortcuts                                    │
│     └─ localStorage prefs                                    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Processing Pipeline Detail

```
Input: video.mp4 (H.264 video, multiple audio tracks)
│
├─ Step 1: Validation (< 1 second)
│  ├─ Check extension
│  ├─ Check file size
│  └─ FFprobe: Verify H.264 codec
│     ├─ If H.264 → Continue
│     └─ If not → REJECT
│
├─ Step 2: Metadata Extraction (< 1 second)
│  ├─ Duration
│  ├─ Resolution (width x height)
│  ├─ Frame rate
│  ├─ Audio track count
│  └─ Audio track details (language, codec, etc.)
│
├─ Step 3: Video Stream Extraction (fast, no re-encoding)
│  │
│  └─ FFmpeg command:
│     ffmpeg -i input.mp4 -map 0:v:0 -c:v copy -an
│            -f hls -hls_time 6 -hls_list_size 0
│            -hls_segment_filename "video_segment_%03d.ts"
│            video_only.m3u8
│     │
│     └─ Output:
│        ├─ video_only.m3u8 (playlist)
│        └─ video_segment_*.ts (H.264 segments, no quality loss)
│
├─ Step 4: Audio Track Processing (parallel for each track)
│  │
│  ├─ Track 0 (English):
│  │  └─ FFmpeg command:
│  │     ffmpeg -i input.mp4 -map 0:a:0 -c:a aac -b:a 128k
│  │            -ac 2 -ar 48000 -profile:a aac_low
│  │            -f hls -hls_time 6 -hls_list_size 0
│  │            -hls_segment_filename "audio_0_segment_%03d.ts"
│  │            audio_track_0.m3u8
│  │     │
│  │     └─ Output:
│  │        ├─ audio_track_0.m3u8
│  │        └─ audio_0_segment_*.ts (AAC 128k stereo)
│  │
│  └─ Track 1 (Spanish):
│     └─ FFmpeg command: (same as above, map 0:a:1)
│        │
│        └─ Output:
│           ├─ audio_track_1.m3u8
│           └─ audio_1_segment_*.ts
│
├─ Step 5: Master Playlist Generation (< 1 second)
│  │
│  └─ Generate playlist_master.m3u8:
│     #EXTM3U
│     #EXT-X-VERSION:3
│     #EXT-X-INDEPENDENT-SEGMENTS
│     #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",
│                LANGUAGE="eng",NAME="English",
│                DEFAULT=YES,URI="audio_track_0.m3u8"
│     #EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",
│                LANGUAGE="spa",NAME="Spanish",
│                DEFAULT=NO,URI="audio_track_1.m3u8"
│     #EXT-X-STREAM-INF:BANDWIDTH=4000000,
│                CODECS="avc1.640029,mp4a.40.2",
│                AUDIO="audio"
│     video_only.m3u8
│
└─ Step 6: Thumbnail Generation (< 1 second)
   │
   └─ FFmpeg command:
      ffmpeg -ss 00:00:10 -i input.mp4 -vframes 1 -q:v 2
             thumb.jpg
      │
      └─ Output: thumb.jpg (at 10% timestamp)

Total Time: 5-10 minutes for full-length video
           (mostly audio conversion time)
```

## Technology Stack Summary

```
┌─────────────────────────────────────────────────────┐
│                  Backend Stack                       │
├─────────────────────────────────────────────────────┤
│ • Python 3.10+                                      │
│ • Flask 3.0.0         (Web framework)               │
│ • Waitress 2.1.2      (WSGI server)                 │
│ • SQLite              (Database)                    │
│ • FFmpeg 5.1+         (Video processing)            │
│ • Threading           (Background workers)          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  Frontend Stack                      │
├─────────────────────────────────────────────────────┤
│ • Jinja2              (Template engine)             │
│ • Video.js 8.10+      (Video player)                │
│ • Vanilla JavaScript  (No frameworks)               │
│ • Custom CSS          (Modern design)               │
│ • Google Fonts        (Typography)                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                  Video Stack                         │
├─────────────────────────────────────────────────────┤
│ • H.264 (AVC)         (Video codec)                 │
│ • AAC LC              (Audio codec)                 │
│ • HLS                 (Streaming protocol)          │
│ • MPEG-TS             (Container format)            │
│ • M3U8                (Playlist format)             │
└─────────────────────────────────────────────────────┘
```

## Deployment Architecture (Production)

```
┌────────────────────────────────────────────────────────────┐
│                      Internet                               │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                 Reverse Proxy (nginx/Apache)                │
│                                                             │
│  • HTTPS/SSL termination                                   │
│  • Static file caching                                     │
│  • Load balancing (optional)                               │
│  • Rate limiting                                           │
└─────────────────────────┬──────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│              xenXgon Play Application                       │
│              (Waitress + Flask)                             │
│                                                             │
│  • Video upload handling                                   │
│  • API endpoints                                           │
│  • File serving                                            │
│  • Background processing                                   │
└──────────┬──────────────────────────────┬──────────────────┘
           │                              │
           ▼                              ▼
┌────────────────────┐         ┌────────────────────┐
│   SQLite Database  │         │  Video Storage     │
│                    │         │  (Local/Cloud)     │
│  • Video metadata  │         │                    │
│  • Audio tracks    │         │  videos/{uuid}/    │
│  • Watch counts    │         │  • Original files  │
└────────────────────┘         │  • HLS streams     │
                               │  • Thumbnails      │
                               └────────────────────┘
```

## Security Considerations

```
┌────────────────────────────────────────────────────────────┐
│                    Security Layers                          │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Input Validation                                        │
│     ├─ File extension whitelist                            │
│     ├─ File size limits (10GB max)                         │
│     ├─ Video codec verification (H.264 only)               │
│     └─ Filename sanitization                               │
│                                                             │
│  2. File Handling                                           │
│     ├─ UUID-based filenames (prevent overwrites)           │
│     ├─ Separate directory per video                        │
│     └─ No executable files                                 │
│                                                             │
│  3. Processing                                              │
│     ├─ FFmpeg timeout limits                               │
│     ├─ Resource limits (2 concurrent jobs)                 │
│     └─ Error handling and cleanup                          │
│                                                             │
│  4. Production (Recommended)                                │
│     ├─ HTTPS/SSL                                           │
│     ├─ Authentication                                       │
│     ├─ CORS restrictions                                   │
│     ├─ Rate limiting                                       │
│     └─ Firewall rules                                      │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

This architecture supports:
- ✅ Fast processing (no video re-encoding)
- ✅ Multi-audio track handling
- ✅ HLS streaming to all devices
- ✅ Scalable background processing
- ✅ TV-optimized user interface
- ✅ RESTful API design
- ✅ Extensible for future features

**Architecture Status:** Production-ready ✅

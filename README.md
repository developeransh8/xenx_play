# xenx_play - Full-Stack Video Streaming Platform

xenx_play is an end-to-end streaming workspace that lets you ingest H.264 movies, process multi-language audio, and serve adaptive HLS playback to every device from a single Windows 11 machine. The project combines three deployable parts:

- xenXgon Play (Flask + SQLite) - the core uploader, worker queue, and TV-friendly web UI.
- FastAPI microservice - a heartbeat/status API that persists events to MongoDB.
- React frontend scaffold - a modern SPA starter that can evolve into a richer consumer experience.

---

## Feature Highlights

- **H.264-first pipeline** - Enforces codec validation, skips needless video re-encoding, and keeps processing times low.
- **Multi-audio support** - Detects every Dolby or E-AC3 track, converts to AAC HLS playlists, and enables instant language switching.
- **TV optimised UX** - Large, focusable controls, remote-friendly navigation, and keyboard shortcuts already wired in.
- **Background workers** - Threaded queue keeps uploads responsive while FFmpeg extracts video, audio, and thumbnails.
- **Extensible architecture** - Clean separation makes it easy to plug in analytics, authentication, or monitoring.
- **Remote sharing ready** - Plays nicely with ngrok, Cloudflare Tunnel, or Tailscale Serve for off-network viewing.

---

## Repository Layout

```
videoStreamer-main/
├── backend/                # FastAPI app + MongoDB heartbeat demo
│   ├── requirements.txt
│   └── server.py
├── frontend/               # React (CRACO + Tailwind + shadcn/ui)
│   ├── package.json
│   └── src/
│       ├── App.js
│       └── components/ui/  # Radix-based UI primitives
├── xenxgon_play/           # Primary Flask streaming application
│   ├── app.py              # Routes for dashboard, upload, watch
│   ├── worker.py           # FFmpeg-powered processing queue
│   ├── database.py         # SQLite storage and helpers
│   ├── utils/ffmpeg.py     # Wrappers around ffprobe/ffmpeg
│   ├── templates/          # Jinja templates (dashboard, upload, watch)
│   ├── static/             # CSS/JS assets and Video.js setup
│   └── run.py              # Waitress production entry point
└── README.md
```

---

## Prerequisites

| Tool | Purpose | Minimum Version |
|------|---------|-----------------|
| Python | xenXgon Play backend + workers | 3.10 |
| FFmpeg / FFprobe | Media analysis, HLS extraction, thumbnails | 6.0 |
| Node.js + Yarn (optional) | React frontend development | Node 18, Yarn 1.22 |
| MongoDB (optional) | FastAPI heartbeat service | 6.x |

> Windows PATH reminder: after installing FFmpeg, add `<FFMPEG>\bin` to PATH so both `ffmpeg` and `ffprobe` are available globally.

---

## Quick Start (xenXgon Play)

1. **Create a virtual environment**
   ```powershell
   cd xenxgon_play
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Launch the streaming server**
   ```powershell
   python run.py
   ```

4. **Open the dashboard**
   Visit http://localhost:8000/dashboard to upload a H.264 movie (`.mp4`, `.mkv`, `.mov`, `.m4v`, `.ts`, `.m2ts`, `.webm`). Tracking and playback controls are live immediately.

The worker queue runs inside the Flask process and can execute multiple conversion jobs concurrently (see `MAX_CONCURRENT_JOBS` in `config.py`).

---

## Share the Stream Outside Your LAN

By default the server only listens on localhost. Use one of the following to project it onto the public internet:

### Option A - ngrok (quickest)
```powershell
ngrok config add-authtoken <your-token>
ngrok http 8000
```
ngrok returns a URL similar to `https://sample.ngrok-free.app`. Share `https://sample.ngrok-free.app/watch/<video-id>` with viewers. Leave ngrok running while they watch.

### Option B - Cloudflare Tunnel
```powershell
cloudflared tunnel --url http://localhost:8000
```
Cloudflare prints a `https://<name>.trycloudflare.com` URL. No port forwarding or firewall changes required.

### Option C - Tailscale Serve (private mesh)
```powershell
tailscale serve https 443 http://localhost:8000
```
Only devices on your Tailscale tailnet can access the link, making it perfect for private family sharing.

> Once the tunnel closes, external links stop working. For long lived access consider deploying to a VPS or cloud platform with HTTPS and authentication.

---

## Optional Services

### FastAPI Heartbeat API
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 9000
```
Create a `.env` next to `server.py`:
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=xenx_status
```
Endpoints:
- `GET /api/` -> `{"message": "Hello World"}`
- `POST /api/status` -> create a heartbeat document
- `GET /api/status` -> list recent heartbeats

### React Frontend Starter
```powershell
cd frontend
yarn install
yarn start
```
Set `REACT_APP_BACKEND_URL` in `frontend/.env` to point at your FastAPI service and build out a richer SPA when ready.

---

## Processing Pipeline (inside `worker.py`)

1. Validate extension, file size, and codec using ffprobe.
2. Copy the H.264 video stream into HLS segments without re-encoding.
3. Convert every audio track to AAC stereo at 48 kHz and generate per-track playlists.
4. Assemble a master playlist mapping the video stream and all audio variants.
5. Capture a thumbnail roughly 10 percent into the movie.
6. Update SQLite with status, metadata, and asset paths. Errors push the job into a `failed` state with an attached message.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Upload rejected instantly | FFmpeg or ffprobe missing | Install FFmpeg 6+ and add to PATH |
| "Video codec must be H.264" | Source is HEVC/VP9 | Re-encode with `ffmpeg -c:v libx264` before uploading |
| Buffering on remote devices | Limited upload bandwidth or tunnel latency | Lower bitrate/resolution, use wired network, or deploy to a VPS |
| Audio switch does nothing | Player has not loaded audio tracks yet | Allow playback to start, then re-select; confirm movie has multiple tracks |
| HTTP 413 errors | Waitress body size limit | Already expanded in `run.py`, ensure you restarted the server |

---

## Packaging and Publication

1. Verify `venv/` and other generated assets remain excluded by `.gitignore`.
2. Inspect changes with `git status` and format or lint as desired.
3. Commit your work (`git add .` then `git commit -m "Add xenx_play streaming platform"`).
4. Push to GitHub (instructions in the next section).

---

## Roadmap Ideas

- Add a bitrate ladder (1080p, 720p, 480p) for networks with limited bandwidth.
- Ship downloadable previews and chapter markers.
- Build an authenticated viewer portal with watch history.
- Expose a REST/GraphQL API for managing libraries remotely.
- Containerise the stack for one-command deployment to cloud providers.

---

## Contributing

Contributions, bug reports, and feature requests are welcome. Open an issue to discuss new ideas or submit a pull request with your enhancements.

---

Enjoy building with **xenx_play** and happy streaming!
*** End Patch

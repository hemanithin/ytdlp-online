# ytdlp.online API Wrapper

A FastAPI-based wrapper for the [ytdlp.online](https://ytdlp.online) service that provides a clean REST API interface for downloading videos using yt-dlp.

## Features

- 🚀 **Three API Approaches**:
  - **Generic Endpoint** - User-friendly query parameters for common use cases
  - **Custom Endpoint** - Full control with raw yt-dlp parameters
  - **Synchronous Endpoint** - Wait for completion and get download URL directly
  
- 📡 **Real-time Progress** - Server-Sent Events (SSE) streaming for live download progress
- 🎵 **Audio Extraction** - Download audio-only with format conversion
- 📺 **Playlist Support** - Download entire playlists or specific items
- 🌐 **CORS Enabled** - Ready for web application integration
- 📝 **Auto Documentation** - Interactive API docs with Swagger UI

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ytdlp-online
```

2. **Create virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment** (optional):
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Usage

### Start the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or run directly:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## API Endpoints

### 1. Generic Download (SSE Streaming)

**Endpoint**: `POST /api/download`

Download videos with user-friendly query parameters and real-time progress streaming.

**Example**:
```bash
curl -N "http://localhost:8000/api/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=720p&format=mp4"
```

**Query Parameters**:
- `url` (required) - Video URL to download
- `format` - Video format (best, worst, mp4, webm)
- `quality` - Quality selection (best, 1080p, 720p, 480p)
- `audio_only` - Extract audio only (boolean)
- `audio_format` - Audio format (mp3, aac, m4a)
- `playlist` - Download entire playlist (boolean)
- `playlist_items` - Specific playlist items (e.g., "1-5,8,10-12")
- `subtitles` - Download subtitles (boolean)
- `subtitle_lang` - Subtitle language code (e.g., "en", "es")

### 2. Custom Download (SSE Streaming)

**Endpoint**: `POST /api/download/custom`

Full control with raw yt-dlp parameters.

**Example**:
```bash
curl -X POST "http://localhost:8000/api/download/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "params": ["-f", "bestvideo+bestaudio", "--merge-output-format", "mp4"]
  }'
```

### 3. Synchronous Download

**Endpoint**: `POST /api/download/sync`

Wait for download completion and get the download URL directly.

**Example**:
```bash
curl -X POST "http://localhost:8000/api/download/sync?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=720p"
```

**Response**:
```json
{
  "status": "completed",
  "download_url": "https://ytdlp.online/download/video.mp4",
  "filename": "video.mp4",
  "message": "Download completed successfully",
  "progress": {
    "status": "completed",
    "message": "100% of 4.24MiB",
    "percent": 100.0
  }
}
```

### 4. Get Help

**Endpoint**: `GET /api/help`

Retrieve yt-dlp help information to discover available options.

**Example**:
```bash
curl "http://localhost:8000/api/help"
```

### 5. Health Check

**Endpoint**: `GET /api/health`

Check API health status.

**Example**:
```bash
curl "http://localhost:8000/api/health"
```

## Configuration

Environment variables (`.env` file):

```env
# ytdlp.online API Configuration
YTDLP_ONLINE_URL=https://ytdlp.online

# Download timeout in seconds (for synchronous endpoint)
DOWNLOAD_TIMEOUT=300

# API Configuration
API_TITLE=ytdlp.online API Wrapper
API_VERSION=1.0.0
API_DESCRIPTION=FastAPI wrapper for ytdlp.online service

# CORS Configuration (comma-separated origins)
CORS_ORIGINS=*

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## Project Structure

```
ytdlp-online/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── models/
│   ├── __init__.py
│   └── schemas.py        # Pydantic models
├── services/
│   ├── __init__.py
│   └── ytdlp_client.py   # ytdlp.online client
├── routers/
│   ├── __init__.py
│   └── download.py       # Download endpoints
└── reference/            # Reference files
    ├── ytdlp_online._help.txt
    └── ytdlp_vido download.txt
```

## Examples

### Download Audio Only (MP3)

```bash
curl -N "http://localhost:8000/api/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&audio_only=true&audio_format=mp3"
```

### Download Playlist Items

```bash
curl -N "http://localhost:8000/api/download?url=https://www.youtube.com/playlist?list=PLxxx&playlist=true&playlist_items=1-5"
```

### Download with Subtitles

```bash
curl -N "http://localhost:8000/api/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&subtitles=true&subtitle_lang=en"
```

### Synchronous Download (Get URL)

```bash
curl -X POST "http://localhost:8000/api/download/sync?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=best"
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style

This project follows PEP 8 guidelines. Format code with:

```bash
pip install black
black .
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The amazing video downloader
- [ytdlp.online](https://ytdlp.online) - Online yt-dlp service
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
# ytdlp-online

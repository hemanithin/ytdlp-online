from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from enum import Enum


class DownloadStatus(str, Enum):
    """Download status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class DownloadRequest(BaseModel):
    """Generic download request with friendly parameters."""
    
    url: str = Field(..., description="Video URL to download")
    format: Optional[str] = Field(None, description="Video format (e.g., best, worst, mp4, webm)")
    quality: Optional[str] = Field(None, description="Quality selection (e.g., best, 1080p, 720p, 480p)")
    audio_only: bool = Field(False, description="Extract audio only")
    audio_format: Optional[str] = Field(None, description="Audio format (e.g., mp3, aac, m4a)")
    playlist: bool = Field(False, description="Download entire playlist")
    playlist_items: Optional[str] = Field(None, description="Specific playlist items (e.g., 1-5,8,10-12)")
    output_template: Optional[str] = Field(None, description="Custom output filename template")
    subtitles: bool = Field(False, description="Download subtitles")
    subtitle_lang: Optional[str] = Field(None, description="Subtitle language code (e.g., en, es)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "format": "mp4",
                "quality": "720p",
                "audio_only": False
            }
        }


class CustomDownloadRequest(BaseModel):
    """Custom download request with raw yt-dlp parameters."""
    
    url: str = Field(..., description="Video URL to download")
    params: List[str] = Field(default_factory=list, description="Array of yt-dlp command-line parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "params": ["-f", "bestvideo+bestaudio", "--merge-output-format", "mp4"]
            }
        }


class DownloadProgress(BaseModel):
    """Download progress information."""
    
    status: DownloadStatus
    message: str
    percent: Optional[float] = None
    eta: Optional[str] = None
    speed: Optional[str] = None


class DownloadResponse(BaseModel):
    """Synchronous download response."""
    
    status: DownloadStatus
    download_url: Optional[str] = Field(None, description="Direct download link from ytdlp.online")
    filename: Optional[str] = Field(None, description="Downloaded file name")
    message: str
    progress: Optional[DownloadProgress] = None
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }

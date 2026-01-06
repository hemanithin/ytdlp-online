import httpx
import re
from typing import AsyncGenerator, Optional, Dict, List
from urllib.parse import quote
from models.schemas import DownloadRequest, DownloadStatus, DownloadProgress
from utils import get_logger

logger = get_logger(__name__)


class YtdlpClient:
    """Client for interacting with ytdlp.online API."""
    
    def __init__(self, base_url: str, download_base_url: Optional[str] = None, timeout: int = 300):
        """
        Initialize the ytdlp.online client.
        
        Args:
            base_url: Base URL for ytdlp.online API
            download_base_url: Base URL for download links (defaults to base_url if not specified)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.download_base_url = (download_base_url or base_url).rstrip('/')
        self.timeout = timeout
        
        logger.info(
            f"YtdlpClient initialized: base_url={self.base_url}, "
            f"download_base_url={self.download_base_url}, timeout={self.timeout}s"
        )
    
    def build_command_from_request(self, request: DownloadRequest) -> str:
        """
        Build yt-dlp command from DownloadRequest parameters.
        
        Args:
            request: Download request with parameters
            
        Returns:
            yt-dlp command string
        """
        logger.debug(f"Building command from request: url={request.url}")
        parts = ["yt-dlp"]
        
        # Format selection
        if request.audio_only:
            logger.debug("Adding audio extraction options")
            parts.append("-x")  # Extract audio
            if request.audio_format:
                logger.debug(f"Audio format: {request.audio_format}")
                parts.extend(["--audio-format", request.audio_format])
        elif request.format:
            # Handle quality-based format selection
            if request.quality:
                logger.debug(f"Quality-based format selection: {request.quality}")
                if request.quality.lower() == "best":
                    parts.extend(["-f", "bestvideo+bestaudio/best"])
                elif request.quality.endswith("p"):
                    # e.g., 720p, 1080p
                    height = request.quality[:-1]
                    parts.extend(["-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"])
            else:
                logger.debug(f"Format: {request.format}")
                parts.extend(["-f", request.format])
        
        # Playlist options
        if not request.playlist:
            logger.debug("Disabling playlist download")
            parts.append("--no-playlist")
        if request.playlist_items:
            logger.debug(f"Playlist items: {request.playlist_items}")
            parts.extend(["-I", request.playlist_items])
        
        # Subtitle options
        if request.subtitles:
            logger.debug("Enabling subtitles")
            parts.append("--write-subs")
            if request.subtitle_lang:
                logger.debug(f"Subtitle language: {request.subtitle_lang}")
                parts.extend(["--sub-lang", request.subtitle_lang])
        
        # Output template
        if request.output_template:
            logger.debug(f"Output template: {request.output_template}")
            parts.extend(["-o", request.output_template])
        
        # Add URL
        parts.append(request.url)
        
        command = " ".join(parts)
        logger.info(f"Built command: {command}")
        return command
    
    def _transform_download_urls(self, data: str) -> str:
        """
        Transform relative download URLs to absolute URLs.
        
        Args:
            data: HTML or text data that may contain download URLs
            
        Returns:
            Transformed data with absolute URLs
        """
        # Pattern to match href="/download/..." in HTML
        pattern = r'href="(/download/[^"]+)"'
        
        def replace_url(match):
            relative_path = match.group(1)
            absolute_url = f"{self.download_base_url}{relative_path}"
            logger.debug(f"Transforming URL: {relative_path} -> {absolute_url}")
            return f'href="{absolute_url}"'
        
        transformed = re.sub(pattern, replace_url, data)
        return transformed
    
    def build_custom_command(self, url: str, params: List[str]) -> str:
        """
        Build yt-dlp command from custom parameters.
        
        Args:
            url: Video URL
            params: List of yt-dlp parameters
            
        Returns:
            yt-dlp command string
        """
        logger.debug(f"Building custom command: url={url}, params={params}")
        parts = ["yt-dlp"] + params + [url]
        command = " ".join(parts)
        logger.info(f"Built custom command: {command}")
        return command
    
    async def stream_download(self, command: str) -> AsyncGenerator[str, None]:
        """
        Stream download progress from ytdlp.online.
        
        Args:
            command: yt-dlp command to execute
            
        Yields:
            Server-Sent Event data lines
        """
        # URL encode the command
        encoded_command = quote(command)
        url = f"{self.base_url}/stream?command={encoded_command}"
        
        logger.info(f"Starting SSE stream to ytdlp.online: {self.base_url}/stream")
        logger.debug(f"Full SSE URL: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.debug(f"HTTP client created with timeout: {self.timeout}s")
                
                async with client.stream("GET", url) as response:
                    logger.info(f"SSE connection established: status={response.status_code}")
                    logger.debug(f"Response headers: {dict(response.headers)}")
                    response.raise_for_status()
                    
                    line_count = 0
                    async for line in response.aiter_lines():
                        if line:
                            line_count += 1
                            logger.debug(f"SSE line {line_count}: {line[:100]}...")
                            
                            # Transform download URLs in data lines
                            if line.startswith("data: "):
                                data_content = line[6:]
                                transformed_data = self._transform_download_urls(data_content)
                                line = f"data: {transformed_data}"
                                logger.debug(f"SSE data event (transformed): {line[6:50]}...")
                            elif line.startswith("event: "):
                                logger.debug(f"SSE event type: {line[7:]}")
                            elif line.startswith("id: "):
                                logger.debug(f"SSE event ID: {line[4:]}")
                            
                            yield line
                    
                    logger.info(f"SSE stream completed: {line_count} lines received")
        
        except httpx.TimeoutException as e:
            logger.error(f"SSE stream timeout after {self.timeout}s: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"SSE stream HTTP error: status={e.response.status_code}, body={e.response.text[:200]}")
            raise
        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            raise
    
    async def download_sync(self, command: str) -> Dict[str, any]:
        """
        Download synchronously and wait for completion.
        
        Args:
            command: yt-dlp command to execute
            
        Returns:
            Dictionary with download results
        """
        logger.info(f"Starting synchronous download with command: {command}")
        
        result = {
            "status": DownloadStatus.PENDING,
            "download_url": None,
            "filename": None,
            "message": "Starting download...",
            "progress": None
        }
        
        last_progress = None
        
        try:
            line_count = 0
            async for line in self.stream_download(command):
                line_count += 1
                
                # Parse SSE format
                if line.startswith("data: "):
                    data = line[6:].strip()
                    logger.debug(f"Sync download data [{line_count}]: {data[:100]}...")
                    
                    # Extract download URL from completion message
                    # Format (now absolute): <a href="https://ytdlp.online/download/filename.mp4" target="_blank">Download File</a>
                    # The URL is already transformed to absolute by stream_download
                    url_match = re.search(r'href="(https?://[^"]+/download/[^"]+)"', data)
                    if url_match:
                        result["download_url"] = url_match.group(1)
                        logger.info(f"Download URL extracted: {result['download_url']}")
                        
                        # Extract filename from the full URL
                        filename_match = re.search(r'/download/(.+)$', result["download_url"])
                        if filename_match:
                            # URL decode the filename
                            from urllib.parse import unquote
                            result["filename"] = unquote(filename_match.group(1))
                            logger.info(f"Filename extracted: {result['filename']}")
                    
                    # Extract progress information
                    # Format: [download]  50.0% of 4.24MiB at 500KiB/s ETA 00:04
                    progress_match = re.search(r'\[download\]\s+(\d+\.?\d*)%\s+of\s+([\d.]+\w+)', data)
                    if progress_match:
                        percent = float(progress_match.group(1))
                        size = progress_match.group(2)
                        
                        logger.info(f"Download progress: {percent}% of {size}")
                        
                        last_progress = DownloadProgress(
                            status=DownloadStatus.DOWNLOADING,
                            message=f"{percent}% of {size}",
                            percent=percent
                        )
                        result["status"] = DownloadStatus.DOWNLOADING
                    
                    # Check for completion
                    if "Command execution completed" in data or "100%" in data:
                        result["status"] = DownloadStatus.COMPLETED
                        result["message"] = "Download completed successfully"
                        logger.info("Download completed successfully")
                        
                        if last_progress:
                            last_progress.status = DownloadStatus.COMPLETED
                            result["progress"] = last_progress.model_dump()
                        break
                    
                    # Check for errors
                    if "error" in data.lower() or "failed" in data.lower():
                        result["status"] = DownloadStatus.FAILED
                        result["message"] = data
                        logger.error(f"Download failed: {data}")
                        
                        if last_progress:
                            last_progress.status = DownloadStatus.FAILED
                            result["progress"] = last_progress.model_dump()
                        break
                
                elif line.startswith("event: close"):
                    # Stream closed
                    logger.info("SSE stream closed event received")
                    if result["status"] == DownloadStatus.PENDING:
                        result["status"] = DownloadStatus.COMPLETED
                        result["message"] = "Download completed"
                    break
            
            logger.info(
                f"Sync download finished: status={result['status']}, "
                f"lines_processed={line_count}, "
                f"download_url={'present' if result['download_url'] else 'missing'}"
            )
        
        except httpx.TimeoutException:
            result["status"] = DownloadStatus.FAILED
            result["message"] = f"Download timeout after {self.timeout} seconds"
            logger.error(f"Download timeout after {self.timeout}s")
        except Exception as e:
            result["status"] = DownloadStatus.FAILED
            result["message"] = f"Download failed: {str(e)}"
            logger.error(f"Download failed with exception: {e}", exc_info=True)
        
        return result
    
    def parse_sse_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Parse a Server-Sent Event line.
        
        Args:
            line: SSE line to parse
            
        Returns:
            Dictionary with event type and data, or None
        """
        if line.startswith("data: "):
            return {"type": "data", "content": line[6:].strip()}
        elif line.startswith("event: "):
            return {"type": "event", "content": line[7:].strip()}
        return None

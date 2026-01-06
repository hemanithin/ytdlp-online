from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from models.schemas import (
    DownloadRequest,
    CustomDownloadRequest,
    DownloadResponse,
    DownloadStatus
)
from services.ytdlp_client import YtdlpClient
from config import settings
from utils import get_logger, get_sse_logger

logger = get_logger(__name__)
sse_logger = get_sse_logger(logger)

router = APIRouter(prefix="/api", tags=["download"])

# Initialize ytdlp client
ytdlp_client = YtdlpClient(
    base_url=settings.ytdlp_online_url,
    download_base_url=settings.effective_download_base_url,
    timeout=settings.download_timeout
)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    return {
        "status": "healthy",
        "service": "ytdlp-online-api",
        "version": settings.api_version
    }


@router.api_route("/download", methods=["GET", "POST"], response_class=StreamingResponse)
async def download_video(
    url: str = Query(..., description="Video URL to download"),
    format: Optional[str] = Query(None, description="Video format (e.g., best, worst, mp4, webm)"),
    quality: Optional[str] = Query(None, description="Quality selection (e.g., best, 1080p, 720p, 480p)"),
    audio_only: bool = Query(False, description="Extract audio only"),
    audio_format: Optional[str] = Query(None, description="Audio format (e.g., mp3, aac, m4a)"),
    playlist: bool = Query(False, description="Download entire playlist"),
    playlist_items: Optional[str] = Query(None, description="Specific playlist items (e.g., 1-5,8,10-12)"),
    output_template: Optional[str] = Query(None, description="Custom output filename template"),
    subtitles: bool = Query(False, description="Download subtitles"),
    subtitle_lang: Optional[str] = Query(None, description="Subtitle language code (e.g., en, es)")
):
    """
    Download video with generic parameters (SSE streaming).
    
    This endpoint streams download progress using Server-Sent Events (SSE).
    """
    logger.info(f"Generic download request: URL={url}, format={format}, quality={quality}, audio_only={audio_only}")
    
    try:
        # Build request object
        request = DownloadRequest(
            url=url,
            format=format,
            quality=quality,
            audio_only=audio_only,
            audio_format=audio_format,
            playlist=playlist,
            playlist_items=playlist_items,
            output_template=output_template,
            subtitles=subtitles,
            subtitle_lang=subtitle_lang
        )
        logger.debug(f"Download request object: {request}")
        
        # Build command
        command = ytdlp_client.build_command_from_request(request)
        logger.info(f"Built command: {command}")
        
        # Start SSE stream tracking
        stream_id = sse_logger.start_stream()
        logger.info(f"Starting SSE stream: {stream_id}")
        
        # Stream response
        async def event_stream():
            try:
                event_count = 0
                async for line in ytdlp_client.stream_download(command):
                    event_count += 1
                    logger.debug(f"SSE [{stream_id}] Event {event_count}: {line[:100]}...")
                    sse_logger.log_event(stream_id, line)
                    yield f"{line}\n"
                logger.info(f"SSE stream [{stream_id}] completed successfully with {event_count} events")
                sse_logger.end_stream(stream_id, normal=True)
            except Exception as e:
                logger.error(f"SSE stream [{stream_id}] error: {e}", exc_info=True)
                sse_logger.end_stream(stream_id, normal=False)
                raise
        
        logger.debug(f"Returning SSE StreamingResponse for stream {stream_id}")
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        logger.error(f"Download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.post("/download/custom", response_class=StreamingResponse)
async def download_custom(request: CustomDownloadRequest):
    """
    Download video with custom yt-dlp parameters (SSE streaming).
    
    This endpoint allows full control over yt-dlp options and streams progress using SSE.
    """
    logger.info(f"Custom download request: URL={request.url}, params={request.params}")
    
    try:
        # Build command
        command = ytdlp_client.build_custom_command(request.url, request.params)
        logger.info(f"Built custom command: {command}")
        
        # Start SSE stream tracking
        stream_id = sse_logger.start_stream()
        logger.info(f"Starting custom SSE stream: {stream_id}")
        
        # Stream response
        async def event_stream():
            try:
                event_count = 0
                async for line in ytdlp_client.stream_download(command):
                    event_count += 1
                    logger.debug(f"SSE [{stream_id}] Custom event {event_count}: {line[:100]}...")
                    sse_logger.log_event(stream_id, line)
                    yield f"{line}\n"
                logger.info(f"Custom SSE stream [{stream_id}] completed with {event_count} events")
                sse_logger.end_stream(stream_id, normal=True)
            except Exception as e:
                logger.error(f"Custom SSE stream [{stream_id}] error: {e}", exc_info=True)
                sse_logger.end_stream(stream_id, normal=False)
                raise
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    except Exception as e:
        logger.error(f"Custom download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.api_route("/download/sync", methods=["GET", "POST"], response_model=DownloadResponse)
async def download_sync(
    url: str = Query(..., description="Video URL to download"),
    format: Optional[str] = Query(None, description="Video format (e.g., best, worst, mp4, webm)"),
    quality: Optional[str] = Query(None, description="Quality selection (e.g., best, 1080p, 720p, 480p)"),
    audio_only: bool = Query(False, description="Extract audio only"),
    audio_format: Optional[str] = Query(None, description="Audio format (e.g., mp3, aac, m4a)"),
    playlist: bool = Query(False, description="Download entire playlist"),
    playlist_items: Optional[str] = Query(None, description="Specific playlist items (e.g., 1-5,8,10-12)"),
    output_template: Optional[str] = Query(None, description="Custom output filename template"),
    subtitles: bool = Query(False, description="Download subtitles"),
    subtitle_lang: Optional[str] = Query(None, description="Subtitle language code (e.g., en, es)")
):
    """
    Download video synchronously and wait for completion.
    
    This endpoint waits for the download to complete and returns the download URL.
    """
    logger.info(f"Sync download request: URL={url}, format={format}, quality={quality}")
    
    try:
        # Build request object
        request = DownloadRequest(
            url=url,
            format=format,
            quality=quality,
            audio_only=audio_only,
            audio_format=audio_format,
            playlist=playlist,
            playlist_items=playlist_items,
            output_template=output_template,
            subtitles=subtitles,
            subtitle_lang=subtitle_lang
        )
        logger.debug(f"Sync download request object: {request}")
        
        # Build command
        command = ytdlp_client.build_command_from_request(request)
        logger.info(f"Sync download command: {command}")
        
        # Execute synchronous download
        logger.info("Starting synchronous download...")
        result = await ytdlp_client.download_sync(command)
        
        logger.info(
            f"Sync download completed: status={result['status']}, "
            f"download_url={result.get('download_url', 'N/A')}, "
            f"filename={result.get('filename', 'N/A')}"
        )
        
        return DownloadResponse(**result)
    
    except Exception as e:
        logger.error(f"Sync download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/help")
async def get_help():
    """
    Get yt-dlp help information.
    
    Returns the full help text from yt-dlp to discover available options.
    """
    logger.info("Help endpoint accessed")
    
    try:
        command = "yt-dlp --help"
        logger.debug(f"Executing help command: {command}")
        
        help_text = []
        line_count = 0
        async for line in ytdlp_client.stream_download(command):
            if line.startswith("data: "):
                help_text.append(line[6:].strip())
                line_count += 1
        
        logger.info(f"Help text retrieved successfully: {line_count} lines")
        
        return {
            "command": command,
            "help": "\n".join(help_text)
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch help: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch help: {str(e)}")

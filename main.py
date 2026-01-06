from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import router as download_router
from utils import setup_logging, get_logger
import time

# Initialize logging
setup_logging(
    log_level=settings.log_level_int,
    enable_file=settings.enable_log_file,
    log_file=settings.log_file
)

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc"
)

logger.info(f"Initializing {settings.api_title} v{settings.api_version}")


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("=" * 60)
    logger.info(f"Application starting: {settings.api_title}")
    logger.info(f"Version: {settings.api_version}")
    logger.info(f"Host: {settings.host}:{settings.port}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"ytdlp.online URL: {settings.ytdlp_online_url}")
    logger.info(f"Download Base URL: {settings.effective_download_base_url}")
    logger.info(f"Download Timeout: {settings.download_timeout}s")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"File Logging: {'Enabled' if settings.enable_log_file else 'Disabled'}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("=" * 60)
    logger.info("Application shutting down gracefully")
    logger.info("=" * 60)


# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"Request: {request.method} {request.url.path} | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Request query params: {dict(request.query_params)}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Time: {process_time:.3f}s"
    )
    
    return response


# Configure CORS
logger.info(f"Configuring CORS with origins: {settings.cors_origins_list}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
logger.info("Registering download router")
app.include_router(download_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    logger.debug("Root endpoint accessed")
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/api/health",
            "download_streaming": "/api/download",
            "download_custom": "/api/download/custom",
            "download_sync": "/api/download/sync",
            "help": "/api/help"
        }
    }


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting uvicorn server on {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )


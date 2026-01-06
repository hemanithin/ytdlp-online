from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import logging


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ytdlp.online API Configuration
    ytdlp_online_url: str = "https://ytdlp.online"
    download_base_url: str = ""  # Optional: Custom base URL for downloads (defaults to ytdlp_online_url)
    download_timeout: int = 300
    
    @property
    def effective_download_base_url(self) -> str:
        """Get the effective download base URL (custom or default)."""
        return self.download_base_url.rstrip('/') if self.download_base_url else self.ytdlp_online_url.rstrip('/')
    
    # API Configuration
    api_title: str = "ytdlp.online API Wrapper"
    api_version: str = "1.0.0"
    api_description: str = "FastAPI wrapper for ytdlp.online service"
    
    # CORS Configuration
    cors_origins: str = "*"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Logging Configuration
    log_level: str = "INFO"
    enable_log_file: bool = False
    log_file: str = "logs/app.log"
    
    @property
    def log_level_int(self) -> int:
        """Get Python logging level constant from string."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(self.log_level.upper(), logging.INFO)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()

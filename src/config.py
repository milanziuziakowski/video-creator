"""Configuration management for video creator."""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: str = ""
    minimax_api_key: str = ""  # Used for FL2V, TTS, and image generation
    
    # Storage (local only)
    storage_base_path: str = "./storage"
    
    # Database
    db_type: Literal["postgresql"] = "postgresql"
    db_url: str = "postgresql://username:password@localhost:5432/video_creator"
    
    # Paths
    project_root_path: Path = Path("./storage/projects")
    temp_folder: Path = Path("./storage/temp")
    
    # Logging
    log_level: str = "INFO"
    
    # MCP
    mcp_transport: Literal["stdio", "http"] = "stdio"
    mcp_log_level: str = "DEBUG"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.project_root_path.mkdir(parents=True, exist_ok=True)
        self.temp_folder.mkdir(parents=True, exist_ok=True)

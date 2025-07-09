"""
Configuration management for the Lore Video Bot
"""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration class for managing environment variables and settings"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        
        # Load environment variables
        self.load_env_file()
        
        # API Keys
        self.openai_api_key = self._get_required_env("OPENAI_API_KEY")
        self.telegram_bot_token = self._get_required_env("TELEGRAM_BOT_TOKEN")
        self.unsplash_access_key = self._get_required_env("UNSPLASH_ACCESS_KEY")
        
        # YouTube Configuration
        self.youtube_client_id = self._get_required_env("YOUTUBE_CLIENT_ID")
        self.youtube_client_secret = self._get_required_env("YOUTUBE_CLIENT_SECRET")
        self.youtube_credentials_path = os.getenv("YOUTUBE_CREDENTIALS_PATH", "credentials/youtube_credentials.json")
        
        # Google Drive Configuration
        self.drive_credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", "credentials/drive_credentials.json")
        
        # Application Settings
        self.temp_dir = Path("temp")
        self.max_video_duration = 60  # seconds
        self.video_width = 1080
        self.video_height = 1920
        self.audio_quality = "high"
        
        # Game of Thrones specific settings
        self.max_script_length = 500  # words
        self.image_count = 4
        self.image_display_duration = 15  # seconds per image
        
        # Rate limiting
        self.openai_requests_per_minute = 20
        self.unsplash_requests_per_hour = 50
        
    def load_env_file(self):
        """Load environment variables from .env file if it exists"""
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if value and not os.getenv(key):
                            os.environ[key] = value
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _get_optional_env(self, key: str, default: str = "") -> str:
        """Get optional environment variable with default"""
        return os.getenv(key, default)
    
    @property
    def credentials_dir(self) -> Path:
        """Get credentials directory path"""
        cred_dir = Path("credentials")
        cred_dir.mkdir(exist_ok=True)
        return cred_dir
    
    def validate_setup(self) -> list:
        """Validate that all required files and configurations exist"""
        errors = []
        
        # Check credentials files
        youtube_creds = Path(self.youtube_credentials_path)
        if not youtube_creds.exists():
            errors.append(f"YouTube credentials file not found: {youtube_creds}")
            
        drive_creds = Path(self.drive_credentials_path)
        if not drive_creds.exists():
            errors.append(f"Google Drive credentials file not found: {drive_creds}")
        
        # Check temp directory
        if not self.temp_dir.exists():
            try:
                self.temp_dir.mkdir(exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create temp directory: {e}")
        
        return errors

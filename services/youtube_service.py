"""
YouTube upload service using YouTube Data API v3
"""

import asyncio
import logging
import pickle
import os
from pathlib import Path
from typing import Optional
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service for uploading videos to YouTube"""
    
    def __init__(self, config):
        self.config = config
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.api_service_name = 'youtube'
        self.api_version = 'v3'
        self.credentials = None
        self.youtube = None
    
    async def upload_video(self, video_path: str, title: str, description: str) -> Optional[str]:
        """
        Upload video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            
        Returns:
            YouTube video URL if successful, None otherwise
        """
        try:
            # Initialize YouTube service
            await self._initialize_youtube_service()
            
            if not self.youtube:
                logger.error("Failed to initialize YouTube service")
                return None
            
            # Prepare video metadata
            video_metadata = self._prepare_video_metadata(title, description)
            
            # Upload video
            video_id = await self._upload_video_file(video_path, video_metadata)
            
            if video_id:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Video uploaded successfully: {video_url}")
                return video_url
            else:
                logger.error("Video upload failed")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading to YouTube: {e}")
            return None
    
    async def _initialize_youtube_service(self):
        """Initialize YouTube API service with authentication"""
        try:
            creds = await self._get_credentials()
            if creds:
                def build_service():
                    return build(self.api_service_name, self.api_version, credentials=creds)
                
                self.youtube = await asyncio.get_event_loop().run_in_executor(
                    None, build_service
                )
                logger.info("YouTube service initialized successfully")
            else:
                logger.error("Failed to get YouTube credentials")
                
        except Exception as e:
            logger.error(f"Error initializing YouTube service: {e}")
    
    async def _get_credentials(self) -> Optional[Credentials]:
        """Get YouTube API credentials"""
        try:
            creds = None
            token_path = Path(self.config.youtube_credentials_path)
            
            # Load existing credentials
            if token_path.exists():
                def load_creds():
                    return Credentials.from_authorized_user_file(str(token_path), self.scopes)
                
                creds = await asyncio.get_event_loop().run_in_executor(None, load_creds)
            
            # Refresh or create new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    def refresh_creds():
                        creds.refresh(Request())
                    
                    await asyncio.get_event_loop().run_in_executor(None, refresh_creds)
                else:
                    # Create new credentials
                    creds = await self._create_new_credentials()
                
                # Save credentials
                if creds:
                    def save_creds():
                        token_path.parent.mkdir(exist_ok=True)
                        with open(token_path, 'w') as token:
                            token.write(creds.to_json())
                    
                    await asyncio.get_event_loop().run_in_executor(None, save_creds)
            
            return creds
            
        except Exception as e:
            logger.error(f"Error getting credentials: {e}")
            return None
    
    async def _create_new_credentials(self) -> Optional[Credentials]:
        """Create new YouTube API credentials"""
        try:
            # Create client secrets for OAuth flow
            client_config = {
                "installed": {
                    "client_id": self.config.youtube_client_id,
                    "client_secret": self.config.youtube_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"]
                }
            }
            
            def create_flow():
                return InstalledAppFlow.from_client_config(client_config, self.scopes)
            
            flow = await asyncio.get_event_loop().run_in_executor(None, create_flow)
            
            # For automated environments, we'll use device flow
            logger.info("Starting OAuth flow for YouTube authentication...")
            
            def run_local_server():
                return flow.run_local_server(port=0)
            
            creds = await asyncio.get_event_loop().run_in_executor(None, run_local_server)
            
            logger.info("YouTube authentication completed")
            return creds
            
        except Exception as e:
            logger.error(f"Error creating new credentials: {e}")
            return None
    
    def _prepare_video_metadata(self, title: str, description: str) -> dict:
        """
        Prepare video metadata for upload
        
        Args:
            title: Video title
            description: Video description
            
        Returns:
            Video metadata dictionary
        """
        # Enhanced description with hashtags
        enhanced_description = f"{description}\n\n" \
                             f"🐉 Game of Thrones lore and theories\n" \
                             f"⚔️ Explore the world of Westeros and Essos\n\n" \
                             f"#GameOfThrones #GoT #Westeros #Dragons #Shorts #Lore #Fantasy"
        
        metadata = {
            'snippet': {
                'title': title[:100],  # YouTube title limit
                'description': enhanced_description[:5000],  # YouTube description limit
                'tags': [
                    'Game of Thrones', 'GoT', 'Westeros', 'Dragons', 'Fantasy',
                    'Lore', 'Theory', 'Shorts', 'Entertainment', 'TV Show'
                ],
                'categoryId': '24',  # Entertainment category
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en'
            },
            'status': {
                'privacyStatus': 'public',  # Make video public
                'madeForKids': False,
                'selfDeclaredMadeForKids': False
            },
            'contentDetails': {
                'definition': 'hd'
            }
        }
        
        return metadata
    
    async def _upload_video_file(self, video_path: str, metadata: dict) -> Optional[str]:
        """
        Upload video file to YouTube
        
        Args:
            video_path: Path to video file
            metadata: Video metadata
            
        Returns:
            Video ID if successful, None otherwise
        """
        try:
            def upload():
                media = MediaFileUpload(
                    video_path,
                    chunksize=-1,  # Upload in a single chunk
                    resumable=True,
                    mimetype='video/mp4'
                )
                
                request = self.youtube.videos().insert(
                    part=','.join(metadata.keys()),
                    body=metadata,
                    media_body=media
                )
                
                response = None
                while response is None:
                    try:
                        status, response = request.next_chunk()
                        if status:
                            logger.info(f"Upload progress: {int(status.progress() * 100)}%")
                    except HttpError as e:
                        if e.resp.status in [500, 502, 503, 504]:
                            # Retry on server errors
                            logger.warning(f"Server error {e.resp.status}, retrying...")
                            continue
                        else:
                            raise
                
                return response
            
            logger.info("Starting video upload to YouTube...")
            response = await asyncio.get_event_loop().run_in_executor(None, upload)
            
            if 'id' in response:
                video_id = response['id']
                logger.info(f"Video uploaded with ID: {video_id}")
                return video_id
            else:
                logger.error("No video ID in upload response")
                return None
                
        except HttpError as e:
            logger.error(f"HTTP error during upload: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading video file: {e}")
            return None
    
    async def set_video_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Set custom thumbnail for uploaded video
        
        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not Path(thumbnail_path).exists():
                logger.warning("Thumbnail file not found")
                return False
            
            def set_thumbnail():
                media = MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
                request = self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=media
                )
                return request.execute()
            
            await asyncio.get_event_loop().run_in_executor(None, set_thumbnail)
            logger.info(f"Thumbnail set for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}")
            return False

"""
Google Drive service for backing up videos
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
import json

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class DriveService:
    """Service for uploading videos to Google Drive"""
    
    def __init__(self, config):
        self.config = config
        self.scopes = ['https://www.googleapis.com/auth/drive.file']
        self.service = None
        self.folder_id = None  # Will be set to the target folder ID
    
    async def upload_video(self, video_path: str, filename: str) -> Optional[str]:
        """
        Upload video to Google Drive
        
        Args:
            video_path: Path to video file
            filename: Desired filename in Drive
            
        Returns:
            Google Drive shareable link if successful, None otherwise
        """
        try:
            # Initialize Drive service
            await self._initialize_drive_service()
            
            if not self.service:
                logger.error("Failed to initialize Google Drive service")
                return None
            
            # Upload file
            file_id = await self._upload_file(video_path, filename)
            
            if file_id:
                # Make file shareable and get link
                share_link = await self._make_file_shareable(file_id)
                logger.info(f"Video uploaded to Google Drive: {share_link}")
                return share_link
            else:
                logger.error("Drive upload failed")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return None
    
    async def _initialize_drive_service(self):
        """Initialize Google Drive API service"""
        try:
            creds_path = Path(self.config.drive_credentials_path)
            
            if not creds_path.exists():
                logger.error(f"Drive credentials file not found: {creds_path}")
                return
            
            def build_service():
                creds = Credentials.from_service_account_file(
                    str(creds_path), scopes=self.scopes
                )
                return build('drive', 'v3', credentials=creds)
            
            self.service = await asyncio.get_event_loop().run_in_executor(
                None, build_service
            )
            
            logger.info("Google Drive service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Drive service: {e}")
    
    async def _upload_file(self, file_path: str, filename: str) -> Optional[str]:
        """
        Upload file to Google Drive
        
        Args:
            file_path: Local file path
            filename: Filename for Drive
            
        Returns:
            File ID if successful, None otherwise
        """
        try:
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'description': f'Game of Thrones lore video created by LoreVideoBot'
            }
            
            # Add to specific folder if folder_id is set
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]
            
            def upload():
                media = MediaFileUpload(
                    file_path,
                    mimetype='video/mp4',
                    resumable=True
                )
                
                request = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                )
                
                response = None
                while response is None:
                    try:
                        status, response = request.next_chunk()
                        if status:
                            logger.info(f"Drive upload progress: {int(status.progress() * 100)}%")
                    except HttpError as e:
                        if e.resp.status in [500, 502, 503, 504]:
                            logger.warning(f"Server error {e.resp.status}, retrying...")
                            continue
                        else:
                            raise
                
                return response
            
            logger.info("Starting upload to Google Drive...")
            response = await asyncio.get_event_loop().run_in_executor(None, upload)
            
            file_id = response.get('id')
            if file_id:
                logger.info(f"File uploaded to Drive with ID: {file_id}")
                return file_id
            else:
                logger.error("No file ID in Drive upload response")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading file to Drive: {e}")
            return None
    
    async def _make_file_shareable(self, file_id: str) -> Optional[str]:
        """
        Make file shareable and get public link
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Shareable link if successful, None otherwise
        """
        try:
            def make_shareable():
                # Make file publicly viewable
                permission = {
                    'type': 'anyone',
                    'role': 'viewer'
                }
                
                self.service.permissions().create(
                    fileId=file_id,
                    body=permission
                ).execute()
                
                # Get shareable link
                file_info = self.service.files().get(
                    fileId=file_id,
                    fields='webViewLink'
                ).execute()
                
                return file_info.get('webViewLink')
            
            share_link = await asyncio.get_event_loop().run_in_executor(
                None, make_shareable
            )
            
            if share_link:
                logger.info(f"File made shareable: {share_link}")
                return share_link
            else:
                logger.error("Failed to get shareable link")
                return None
                
        except Exception as e:
            logger.error(f"Error making file shareable: {e}")
            return None
    
    async def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Create a folder in Google Drive
        
        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Parent folder ID (optional)
            
        Returns:
            Folder ID if successful, None otherwise
        """
        try:
            if not self.service:
                await self._initialize_drive_service()
            
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            def create_folder():
                return self.service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
            
            folder = await asyncio.get_event_loop().run_in_executor(
                None, create_folder
            )
            
            folder_id = folder.get('id')
            if folder_id:
                logger.info(f"Created folder '{folder_name}' with ID: {folder_id}")
                return folder_id
            else:
                logger.error("Failed to create folder")
                return None
                
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            return None
    
    async def list_files(self, folder_id: Optional[str] = None) -> list:
        """
        List files in Drive folder
        
        Args:
            folder_id: Folder ID to list files from (optional)
            
        Returns:
            List of file metadata
        """
        try:
            if not self.service:
                await self._initialize_drive_service()
            
            query = "trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            def list_files():
                return self.service.files().list(
                    q=query,
                    fields="files(id, name, createdTime, size, webViewLink)"
                ).execute()
            
            results = await asyncio.get_event_loop().run_in_executor(
                None, list_files
            )
            
            files = results.get('files', [])
            logger.info(f"Found {len(files)} files in Drive")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def set_target_folder(self, folder_id: str):
        """
        Set the target folder ID for uploads
        
        Args:
            folder_id: Google Drive folder ID
        """
        self.folder_id = folder_id
        logger.info(f"Set target folder ID: {folder_id}")

# Lore Video Bot

## Overview

This is an automated Telegram bot that creates Game of Thrones lore videos and uploads them to YouTube and Google Drive. The bot generates AI-powered scripts, creates vertical videos (9:16 ratio) optimized for YouTube Shorts, and handles the entire pipeline from content generation to distribution.

## User Preferences

- **Communication style**: Simple, everyday language
- **Video style requirements**: 
  - Strong hooks that grab attention immediately (like "What if I told you...")
  - Cinematic image animations (Ken Burns effect, panning, zooming)
  - Dramatic, engaging voice with strategic pauses
  - YouTube Shorts optimized format matching user's existing channel style
  - Cliffhanger endings and mystery-building throughout

## System Architecture

The application follows a modular service-oriented architecture with clear separation of concerns:

- **Configuration Management**: Centralized configuration handling through environment variables
- **Service Layer**: Distinct services for each major functionality (OpenAI, Image, TTS, Video, YouTube, Drive)
- **Bot Interface**: Telegram bot as the primary user interface
- **Asynchronous Processing**: Built on Python's asyncio for non-blocking operations

### Key Design Decisions

**Problem**: Need to handle multiple external APIs and media processing without blocking user interactions
**Solution**: Asynchronous service architecture with individual service classes
**Rationale**: Allows for concurrent processing and better user experience with real-time progress updates

**Problem**: Video creation requires multiple steps (script generation, image sourcing, TTS, video assembly)
**Solution**: Pipeline approach with each service handling one specific task
**Rationale**: Modular design enables easier testing, maintenance, and future feature additions

## Key Components

### Core Services

1. **OpenAI Service** (`services/openai_service.py`)
   - Generates Game of Thrones lore scripts using GPT-4o model
   - Returns structured JSON with script, title, description, and keywords
   - Handles prompt engineering for Game of Thrones specific content

2. **Image Service** (`services/image_service.py`)
   - Fetches relevant images from Unsplash API
   - Enhances keywords for better search results
   - Downloads and caches images locally

3. **TTS Service** (`services/tts_service.py`)
   - Converts scripts to speech using Google TTS
   - Generates MP3 audio files for video narration
   - Handles text cleanup and optimization for speech

4. **Video Service** (`services/video_service.py`)
   - Creates vertical videos (1080x1920) using FFmpeg
   - Combines images and audio into cohesive videos
   - Optimized for YouTube Shorts format

5. **YouTube Service** (`services/youtube_service.py`)
   - Handles OAuth2 authentication with Google
   - Uploads videos to YouTube with metadata
   - Manages YouTube Data API v3 interactions

6. **Drive Service** (`services/drive_service.py`)
   - Backs up videos to Google Drive
   - Uses service account authentication
   - Provides shareable links for TikTok distribution

7. **Telegram Bot** (`services/telegram_bot.py`)
   - Main user interface for bot interactions
   - Orchestrates the entire video creation pipeline
   - Provides real-time progress updates

### Configuration Management

- **Environment-based Configuration**: All sensitive data stored in environment variables
- **Credential Management**: Separate JSON files for OAuth credentials
- **Runtime Settings**: Video dimensions, quality settings, rate limiting parameters

## Data Flow

1. **User Input**: User sends topic request via Telegram
2. **Script Generation**: OpenAI generates Game of Thrones lore content
3. **Image Sourcing**: Unsplash API fetches relevant thematic images
4. **Audio Generation**: Google TTS converts script to speech
5. **Video Assembly**: FFmpeg combines images and audio into vertical video
6. **Upload Process**: 
   - Primary upload to YouTube with metadata
   - Backup upload to Google Drive
7. **User Notification**: Bot sends completion status and links

## External Dependencies

### APIs and Services
- **OpenAI API**: Script generation using GPT-4o model
- **Telegram Bot API**: User interface and interaction
- **Unsplash API**: Image sourcing and downloads
- **Google TTS**: Text-to-speech conversion
- **YouTube Data API v3**: Video upload and management
- **Google Drive API**: Backup storage

### Media Processing
- **FFmpeg**: Video creation and processing
- **Python Libraries**: 
  - `python-telegram-bot`: Telegram integration
  - `openai`: OpenAI API client
  - `gtts`: Google Text-to-Speech
  - `google-api-python-client`: Google services integration

### Authentication
- **OAuth2**: YouTube API authentication
- **Service Account**: Google Drive authentication
- **API Keys**: OpenAI, Telegram, Unsplash access

## Deployment Strategy

### Local Development
- Environment variables via `.env` file
- Local temp directory for media processing
- Credential files in `credentials/` directory

### Production Considerations
- Secure credential management required
- Adequate storage for temporary media files
- Rate limiting for external APIs
- Error handling and recovery mechanisms

### File Structure
```
temp/               # Temporary media processing files
logs/               # Application logs with rotation
credentials/        # OAuth and service account credentials
services/           # Core service modules
utils/              # Utility functions (logging)
```

### Configuration Requirements
- All API keys must be configured in environment
- YouTube OAuth requires initial authentication flow
- Google Drive service account must have folder access
- FFmpeg must be installed on the system

The application is designed to be self-contained with clear error handling and logging throughout the pipeline.
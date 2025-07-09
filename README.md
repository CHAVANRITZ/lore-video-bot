# Lore Video Bot Setup Guide

An automated Telegram bot that creates Game of Thrones lore videos and uploads them to YouTube and Google Drive with a single command.

## Features

- 🤖 Telegram bot interface with simple commands
- 📝 AI-generated Game of Thrones lore scripts using OpenAI
- 🖼️ Automatic relevant image sourcing from Unsplash
- 🎙️ Text-to-speech conversion using Google TTS
- 🎬 Vertical video creation optimized for YouTube Shorts (9:16 ratio)
- 📺 Automatic YouTube upload with metadata
- 💾 Google Drive backup for TikTok distribution
- 📊 Real-time progress updates during creation

## Setup Instructions

### 1. Environment Setup

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Fill in your API credentials in `.env`:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TELEGRAM_BOT_TOKEN`: Get from @BotFather on Telegram
   - `UNSPLASH_ACCESS_KEY`: Register at Unsplash Developer
   - YouTube credentials (see YouTube setup below)

### 2. YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3 and Google Drive API
4. Create OAuth 2.0 credentials
5. Download the client secret JSON file as `credentials/youtube_client_secret.json`
6. Add your client ID and secret to `.env`

### 3. Google Drive Setup

1. In the same Google Cloud project, create a service account
2. Download the service account JSON file as `credentials/drive_credentials.json`
3. Share your target Google Drive folder with the service account email

### 4. Telegram Bot Setup

1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token to your `.env` file
4. Optionally set bot commands:
   ```
   /start - Generate a Game of Thrones lore video
   /help - Show available commands
   ```

### 5. Installation and Running

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the bot:
   ```bash
   python main.py
   ```

## Usage

1. Start a chat with your bot on Telegram
2. Send `/start` command
3. Follow the prompts to specify your video topic
4. Wait for the bot to create and upload your video
5. Receive links to YouTube and Google Drive

## Video Specifications

- **Format**: MP4, 9:16 aspect ratio (vertical)
- **Duration**: Under 60 seconds (YouTube Shorts compliant)
- **Resolution**: 1080x1920 pixels
- **Audio**: High-quality TTS narration
- **Images**: 3-4 relevant Game of Thrones themed images

## Troubleshooting

### Common Issues

1. **API Rate Limits**: The bot handles rate limits gracefully with retries
2. **Video Processing**: Ensure ffmpeg is installed on your system
3. **Authentication**: Make sure all credentials are correctly set up

### Error Messages

The bot provides detailed error messages for:
- Missing API credentials
- Failed image downloads
- Video processing errors
- Upload failures

## File Structure


"""
Telegram Bot service for handling user interactions
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config
from services.openai_service import OpenAIService
from services.image_service import ImageService
from services.tts_service import TTSService
from services.video_service import VideoService
from services.youtube_service import YouTubeService
from services.drive_service import DriveService

logger = logging.getLogger(__name__)

class LoreVideoBot:
    """Main Telegram bot class for Game of Thrones lore video creation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.application = Application.builder().token(config.telegram_bot_token).build()
        
        # Initialize services
        self.openai_service = OpenAIService(config)
        self.image_service = ImageService(config)
        self.tts_service = TTSService(config)
        self.video_service = VideoService(config)
        self.youtube_service = YouTubeService(config)
        self.drive_service = DriveService(config)
        
        # Setup handlers
        self._setup_handlers()
        
        # Track user sessions
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
    
    def _setup_handlers(self):
        """Setup command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        welcome_message = (
            "🐉 **Welcome to the Game of Thrones Lore Video Bot!** ⚔️\n\n"
            "I can create amazing vertical videos about Game of Thrones lore "
            "and automatically upload them to YouTube and Google Drive.\n\n"
            "**How it works:**\n"
            "1. Tell me what GoT topic you want a video about\n"
            "2. I'll generate an engaging script using AI\n"
            "3. Find relevant images and create narration\n"
            "4. Create a vertical video optimized for YouTube Shorts\n"
            "5. Upload to YouTube and backup to Google Drive\n\n"
            "**Just send me a topic like:**\n"
            "• Why Jon Snow returned from death\n"
            "• The mystery of Azor Ahai\n"
            "• Daenerys' dragon bloodline\n"
            "• The Night King's true purpose\n\n"
            "What Game of Thrones topic would you like a video about?"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        # Initialize user session
        self.user_sessions[user_id] = {
            'state': 'waiting_for_topic',
            'topic': None
        }
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = (
            "🔥 **Game of Thrones Lore Video Bot Help** 🔥\n\n"
            "**Available Commands:**\n"
            "/start - Begin creating a new lore video\n"
            "/help - Show this help message\n\n"
            "**How to use:**\n"
            "1. Use /start to begin\n"
            "2. Send me your desired GoT topic\n"
            "3. Wait for the magic to happen!\n\n"
            "**Video Specifications:**\n"
            "• Duration: Under 60 seconds\n"
            "• Format: Vertical (9:16) for YouTube Shorts\n"
            "• Quality: 1080x1920 HD\n"
            "• Content: AI-generated scripts with relevant images\n\n"
            "**Example Topics:**\n"
            "• Character backstories and theories\n"
            "• Historical events in Westeros\n"
            "• Mysteries and prophecies\n"
            "• House histories and lineages\n"
            "• Dragon lore and magic"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages from users"""
        user_id = update.effective_user.id
        message_text = update.message.text.strip()
        
        # Check if user has an active session
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "Please use /start to begin creating a Game of Thrones lore video!"
            )
            return
        
        session = self.user_sessions[user_id]
        
        if session['state'] == 'waiting_for_topic':
            # User provided a topic
            session['topic'] = message_text
            session['state'] = 'processing'
            
            await update.message.reply_text(
                f"🎬 **Creating video about:** {message_text}\n\n"
                "⏳ This will take a few minutes. I'll keep you updated on the progress!"
            )
            
            # Start video creation process
            await self.create_video(update, context, message_text, user_id)
        
        else:
            await update.message.reply_text(
                "I'm currently processing your request. Please wait for it to complete!"
            )
    
    async def create_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str, user_id: int):
        """Create the complete video and upload to platforms"""
        try:
            # Step 1: Generate script
            await update.message.reply_text("📝 Generating Game of Thrones lore script...")
            script_data = await self.openai_service.generate_got_script(topic)
            
            if not script_data:
                raise Exception("Failed to generate script")
            
            # Step 2: Find images
            await update.message.reply_text("🖼️ Finding relevant images...")
            images = await self.image_service.get_got_images(script_data['keywords'])
            
            if len(images) < 3:
                raise Exception("Insufficient relevant images found")
            
            # Step 3: Generate speech
            await update.message.reply_text("🎙️ Creating narration...")
            audio_file = await self.tts_service.text_to_speech(script_data['script'])
            
            # Step 4: Create video
            await update.message.reply_text("🎬 Creating video...")
            video_file = await self.video_service.create_vertical_video(
                script_data, images, audio_file
            )
            
            # Step 5: Upload to YouTube
            await update.message.reply_text("📺 Uploading to YouTube...")
            youtube_url = await self.youtube_service.upload_video(
                video_file, script_data['title'], script_data['description']
            )
            
            # Step 6: Save to Google Drive
            await update.message.reply_text("💾 Saving to Google Drive...")
            drive_url = await self.drive_service.upload_video(
                video_file, f"{script_data['title']}.mp4"
            )
            
            # Success message
            success_message = (
                f"✅ **Video created successfully!** 🎉\n\n"
                f"**Topic:** {topic}\n"
                f"**Title:** {script_data['title']}\n\n"
                f"🔗 **YouTube:** {youtube_url}\n"
                f"📁 **Google Drive:** {drive_url}\n\n"
                f"Your video is now live and ready to share! 🚀\n"
                f"Use /start to create another video."
            )
            
            await update.message.reply_text(success_message, parse_mode='Markdown')
            
            # Cleanup
            await self._cleanup_files(audio_file, video_file)
            
        except Exception as e:
            logger.error(f"Error creating video for user {user_id}: {e}")
            error_message = (
                f"❌ **Error creating video:** {str(e)}\n\n"
                "Please try again with /start or contact support if the issue persists."
            )
            await update.message.reply_text(error_message, parse_mode='Markdown')
        
        finally:
            # Reset user session
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
    
    async def _cleanup_files(self, *files):
        """Clean up temporary files"""
        for file_path in files:
            if file_path and Path(file_path).exists():
                try:
                    Path(file_path).unlink()
                    logger.info(f"Cleaned up file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup file {file_path}: {e}")
    
    async def start(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Keep the application running
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        try:
            # Keep running indefinitely
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Bot stopped by user")
        finally:
            # Cleanup
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

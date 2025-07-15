import logging
from pathlib import Path
from typing import Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.ext import AIORateLimiter

from config import Config
from services.gemini_service import GeminiService
from services.image_service import ImageService
from services.tts_service import TTSService
from services.video_service import VideoService
from services.youtube_service import YouTubeService
from services.drive_service import DriveService

logger = logging.getLogger(__name__)


class LoreVideoBot:

    def __init__(self, config: Config):
        self.config = config
        self.application = Application.builder() \
            .token(config.telegram_bot_token) \
            .rate_limiter(AIORateLimiter()) \
            .build()

        self.gemini_service = GeminiService(config)
        self.image_service = ImageService(config)
        self.tts_service = TTSService(config)
        self.video_service = VideoService(config)
        self.youtube_service = YouTubeService(config)
        self.drive_service = DriveService(config)

        self.user_sessions: Dict[int, Dict[str, Any]] = {}

        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(
            CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           self.handle_message))

    async def start_command(self, update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
        ...
        # (same as before)

    async def help_command(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        ...
        # (same as before)

    async def handle_message(self, update: Update,
                             context: ContextTypes.DEFAULT_TYPE):
        ...
        # (same as before)

    async def create_video(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE, topic: str,
                           user_id: int):
        ...
        # (same as before)

    async def _cleanup_files(self, *files):
        ...
        # (same as before)

    async def start(self, fastapi_app):
        """Start bot in webhook mode and mount FastAPI route"""
        logger.info("Starting Telegram bot in webhook mode...")

        # Start Telegram application
        await self.application.initialize()
        await self.application.start()

        # Set webhook
        webhook_url = f"{self.config.healthcheck_url.replace('/health', '')}/webhook"
        await self.application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")

        # Mount webhook FastAPI route
        @fastapi_app.post("/webhook")
        async def telegram_webhook(update: dict):
            update = Update.de_json(update, self.application.bot)
            await self.application.process_update(update)
            return {"ok": True}

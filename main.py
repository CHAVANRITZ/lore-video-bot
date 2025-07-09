#!/usr/bin/env python3
"""
Lore Video Bot - Automated Game of Thrones video creation and upload bot
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from services.telegram_bot import LoreVideoBot
from utils.logger import setup_logger

async def main():
    """Main entry point for the Lore Video Bot"""
    
    # Setup logging
    logger = setup_logger()
    
    try:
        # Initialize configuration
        config = Config()
        logger.info("Configuration loaded successfully")
        
        # Create temp directory if it doesn't exist
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Initialize and start the bot
        bot = LoreVideoBot(config)
        logger.info("Starting Lore Video Bot...")
        
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

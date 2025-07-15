#!/usr/bin/env python3
"""
Lore Video Bot - Game of Thrones video automation with healthcheck, webhook support, and uptime resilience
"""

import asyncio
import logging
import os
import sys
import threading
import time
from pathlib import Path
from fastapi import FastAPI, Request
import uvicorn
import requests

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from services.telegram_bot import LoreVideoBot
from utils.logger import setup_logger

# ----------------- FastAPI Setup -----------------

app = FastAPI()
bot: LoreVideoBot = None  # To be initialized in main()


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = bot.application.update_queue.bot.update_de_json(
        data, bot.application.bot)
    await bot.application.process_update(update)
    return {"ok": True}


# ----------------- Auto Ping -----------------


def auto_ping():
    url = os.getenv("HEALTHCHECK_URL")
    if not url:
        logging.warning("HEALTHCHECK_URL not set in .env")
        return

    while True:
        try:
            requests.get(url)
            logging.info(f"Auto-pinged {url}")
        except Exception as e:
            logging.warning(f"Auto-ping failed: {e}")
        time.sleep(300)


# ----------------- Main Async Entry -----------------


async def main():
    global bot
    logger = setup_logger()

    try:
        config = Config()
        logger.info("Configuration loaded successfully")

        # Create temp directory if it doesn't exist
        Path("temp").mkdir(exist_ok=True)

        # Start FastAPI server in a thread
        threading.Thread(target=lambda: uvicorn.run(
            app, host="0.0.0.0", port=8080, log_level="warning"),
                         daemon=True).start()
        logger.info("Healthcheck + Webhook server running on port 8080")

        # Start auto-ping thread
        threading.Thread(target=auto_ping, daemon=True).start()
        logger.info("Auto-ping thread started to prevent Replit sleep")

        # Initialize and start bot in webhook mode
        bot = LoreVideoBot(config)
        await bot.start(app)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in bot: {e}")
        sys.exit(1)


# ----------------- Restart Loop -----------------

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logging.error(f"Main crashed, restarting... Reason: {e}")
            time.sleep(5)

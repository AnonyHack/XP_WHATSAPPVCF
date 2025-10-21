import logging
import asyncio
import sys
import os
from threading import Thread
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, LOG_FILE
from handlers.health_check import run_health_server

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging with UTF-8 encoding for file and error handling for console
class UTF8StreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Ignore encoding errors in console (e.g., for emojis on Windows)
            pass

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        UTF8StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Pyrogram Client
app = Client(
    "WhatsAppStatusBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="handlers")  # Load handlers from handlers/ and submodules
)

async def main():
    logger.info("Starting WhatsApp Status View Increaser Bot...")
    try:
        # Start the health check server in a separate thread
        health_thread = Thread(target=run_health_server, daemon=True)
        health_thread.start()
        logger.info("Health check server thread started")

        # Start the bot
        await app.start()
        logger.info("Bot started successfully")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    app.run(main())
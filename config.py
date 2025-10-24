import os
from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ───── Basic Bot Configuration ───── #
API_ID = int(getenv("API_ID", ""))  # Get from https://my.telegram.org
API_HASH = getenv("API_HASH", "")  # Get from https://my.telegram.org
BOT_TOKEN = getenv("BOT_TOKEN", "")  # Get from @BotFather
BOT_NAME = getenv("BOT_NAME", "WaStatusBot")
BOT_USERNAME = getenv("BOT_USERNAME", "@WaStatusViewsBot")
OWNER_ID = int(getenv("OWNER_ID", "5962658076, 5723483216"))  # Your Telegram user ID
ADMINS = [int(admin_id) for admin_id in getenv("ADMINS", str(OWNER_ID)).split(",")]
# Example additional admin IDs; allow override via ADMIN_IDS env var (comma-separated)
ADMIN_IDS = [int(x) for x in getenv("ADMIN_IDS", "5962658076, 5723483216").split(",")]
OWNER_USERNAME = getenv("OWNER_USERNAME", "@Am_Itachiuchiha")
RENDER_PORT = int(getenv("RENDER_PORT", "10000"))  # Port for health check server

# ───── Mongo & Logging ───── #
MONGO_DB_URI = getenv("MONGO_DB_URI", "mongodb+srv://anonymousguywas:12345Trials@cluster0.t4nmrtp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
MONGO_DB_NAME = getenv("MONGO_DB_NAME", "WaStatusViewsBot")
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "bot.log")

# ───── Channel Configurations ───── #
SUPPORT_GROUP_URL = getenv("SUPPORT_GROUP_URL", "https://t.me/nextgenroom")
SOURCE_CODE_URL = getenv("SOURCE_CODE_URL", "https://t.me/Am_Itachiuchiha")
TUTORIAL_VIDEO_URL = getenv("TUTORIAL_VIDEO_URL", "https://youtube.com/@freenethubtech?si=PJHbpcYOxBdWES0S")

DOWNLOAD_CHANNEL = {
    "name": "VCF Downloads",
    "url": getenv("DOWNLOAD_CHANNEL_URL", "https://t.me/vcfdownload"),
    "chat_id": getenv("DOWNLOAD_CHANNEL_ID", "@vcfdownload")
}

REQUIRED_CHANNELS = [
    {
        "name": "Main Channel",
        "url": getenv("MAIN_CHANNEL_URL", "https://t.me/XPTOOLSTEAM"),
        "chat_id": getenv("MAIN_CHANNEL_ID", "@XPTOOLSTEAM")
    },
    # Add more channels if needed, e.g.:
    # {
    #     "name": "Channel 2",
    #     "url": getenv("CHANNEL_LINK_2", "https://t.me/Channel2"),
    #     "chat_id": getenv("CHANNEL_ID_2", "@Channel2")
    # }
]

# ───── Bot Settings ───── #
WELCOME_MESSAGE = (
    "👋 Welcome to the WhatsApp Status View Increaser Bot!\n\n"
    "📲 Join one of our VCF groups below to share your number and increase your WhatsApp Status views!"
)
WELCOME_IMAGE = getenv("WELCOME_IMAGE", "https://i.ibb.co/xtDy5vw9/whatsappviews.jpg")  # Optional: Add URL to welcome image if desired
DEFAULT_WATERMARK = getenv("DEFAULT_WATERMARK", "🔥")  # Watermark for VCF names
DELETE_DELAY_HOURS = int(getenv("DELETE_DELAY_HOURS", "24"))  # Delay before deleting group data
VCF_FILE_NAME_PATTERN = getenv("VCF_FILE_NAME_PATTERN", "VCF_{limit}_{date}.vcf")
TEMP_VCF_PATH = os.path.join(os.path.dirname(__file__), "data", "temp_vcf")

# ───── File System Setup ───── #
# Ensure directories exist
os.makedirs(TEMP_VCF_PATH, exist_ok=True)

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)





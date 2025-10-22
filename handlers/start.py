import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import WELCOME_MESSAGE, WELCOME_IMAGE, REQUIRED_CHANNELS
from database.users import register_user, update_user_subscription_status
from database.connection import get_db
from handlers.force_join import check_subscription, prompt_subscription

# Setup logging
logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.private)
async def handle_start(client: Client, message):
    """Handle the /start command and display the home page UI."""
    user_id = message.from_user.id
    logger.debug(f"Handling /start for user {user_id}")
    try:
        # Register user in the database
        if not register_user(user_id):
            logger.error(f"Failed to register user {user_id} on start")
            await message.reply_text("❌ An error occurred while starting the bot. Please try again later.")
            return

        # Check if user has passed subscription check
        db = get_db()
        user = db.users.find_one({"user_id": user_id})
        if not user or not user.get("subscribed", False):
            logger.debug(f"User {user_id} not subscribed, checking channel membership")
            if await check_subscription(client, user_id):
                update_user_subscription_status(user_id, True)
                logger.info(f"User {user_id} was already subscribed, updated status")
            else:
                await prompt_subscription(client, message, user_id)
                return

        # Create inline keyboard with buttons arranged in 2 columns
        markup = InlineKeyboardMarkup([
            # First row: two buttons side by side
            [
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                InlineKeyboardButton("📁 My Submissions", callback_data="my_submissions")
            ],
            # Second row: two buttons side by side  
            [
                InlineKeyboardButton("💡 Tutorial", callback_data="tutorial"),
                InlineKeyboardButton("ℹ️ About Bot", callback_data="about_bot")
            ]
        ])

        # Send welcome message with optional image
        if WELCOME_IMAGE:
            try:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=WELCOME_IMAGE,
                    caption=WELCOME_MESSAGE,
                    reply_markup=markup
                )
                logger.info(f"Sent start photo to user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send photo for user {user_id}: {e}")
                await client.send_message(
                    chat_id=message.chat.id,
                    text=WELCOME_MESSAGE,
                    reply_markup=markup
                )
                logger.info(f"Sent start message (fallback) to user {user_id}")
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=WELCOME_MESSAGE,
                reply_markup=markup
            )
            logger.info(f"Sent start message to user {user_id}")
    except Exception as e:
        await message.reply_text(
            "❌ An error occurred. Please try again with /start."
        )
        logger.error(f"Error in /start for user {user_id}: {e}", exc_info=True)

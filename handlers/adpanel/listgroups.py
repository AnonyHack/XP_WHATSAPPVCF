import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from database.connection import get_db

# Setup logging
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    return user_id in ADMIN_IDS

@Client.on_message(filters.command("listgroups") & filters.private)
async def handle_listgroups(client: Client, message):
    """List all active groups with their IDs, limits, current users, and status."""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply_text("🚫 You are not authorized to use this command.")
        logger.warning(f"Unauthorized /listgroups attempt by user {user_id}")
        return

    try:
        db = get_db()
        active_groups = db.groups.find({"status": "active"}).sort("limit", 1)
        groups_list = list(active_groups)
        
        if not groups_list:
            await message.reply_text(
                "No active groups found.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
                ])
            )
            logger.info(f"No active groups found for /listgroups by user {user_id}")
            return

        message_text = "📋 Active Groups:\n\n"
        for group in groups_list:
            message_text += (
                f"Group ID: {group['group_id']}\n"
                f"Limit: {group['limit']}\n"
                f"Current Users: {group['current_users']}\n"
                f"Status: {group['status'].capitalize()}\n\n"
            )

        await message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        logger.info(f"Listed {len(groups_list)} active groups for user {user_id}")
    except Exception as e:
        await message.reply_text(
            "❌ An error occurred while listing active groups. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        logger.error(f"Error listing active groups for user {user_id}: {e}", exc_info=True)
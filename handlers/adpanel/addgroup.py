import logging
from pyrogram import Client, filters
from config import ADMIN_IDS
from database.groups import add_group

# Setup logging
logger = logging.getLogger(__name__)

@Client.on_message(filters.command("addgroup") & filters.user(ADMIN_IDS) & filters.private)
async def add_group_command(client: Client, message):
    """Handle the /addgroup command to add a new VCF group."""
    logger.debug(f"Handling /addgroup for admin {message.from_user.id}")
    try:
        # Check if limit is provided
        if len(message.command) < 2:
            await message.reply_text("❌ Usage: /addgroup <limit>\nExample: /addgroup 10000")
            logger.warning(f"Admin {message.from_user.id} used /addgroup without limit")
            return

        # Parse limit
        try:
            limit = int(message.command[1])
            if limit <= 0:
                raise ValueError("Limit must be a positive integer")
        except ValueError:
            await message.reply_text("❌ Invalid limit. Please provide a positive number.")
            logger.warning(f"Admin {message.from_user.id} provided invalid limit: {message.command[1]}")
            return

        # Add group to database
        if add_group(limit):
            group_id = f"ID-XP{limit}GROUP"
            await message.reply_text(f"✅ Successfully added group {group_id} with limit {limit} users.")
            logger.info(f"Admin {message.from_user.id} added group {group_id}")
        else:
            await message.reply_text(f"❌ Failed to add group with limit {limit}. It may already exist.")
            logger.warning(f"Failed to add group with limit {limit} for admin {message.from_user.id}")
    except Exception as e:
        await message.reply_text("❌ Error adding group. Please try again.")
        logger.error(f"Error adding group for admin {message.from_user.id}: {e}", exc_info=True)
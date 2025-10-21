import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS
from database.groups import get_all_groups

# Setup logging
logger = logging.getLogger(__name__)

# Store pagination state (admin_id -> current_page)
pagination_state = {}

def get_paginated_groups(group_list, page, per_page=2):
    """Return a slice of groups for the given page and navigation buttons."""
    total_groups = len(group_list)
    total_pages = (total_groups + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_groups)
    current_groups = group_list[start_idx:end_idx]

    # Build message text for current page
    message_text = "📊 VCF Group Statistics:\n\n"
    for group in current_groups:
        group_id = group.get("group_id", "Unknown")
        limit = group.get("limit", 0)
        current_users = group.get("current_users", 0)
        status = group.get("status", "Unknown")
        status_text = {
            "active": "📥 Active",
            "full": "⏳ Full",
            "approved": "✅ Approved"
        }.get(status, f"❓ {status}")
        message_text += (
            f"Group: {group_id}\n"
            f"Limit: {limit} Users\n"
            f"Members: {current_users}/{limit}\n"
            f"Status: {status_text}\n\n"
        )

    message_text += f"Page {page + 1}/{total_pages} | Total Groups: {total_groups}"

    # Create navigation buttons
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"gpstats_back_{page}"))
    if end_idx < total_groups:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"gpstats_next_{page}"))
    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

    return message_text, reply_markup

@Client.on_message(filters.command("gpstats") & filters.user(ADMIN_IDS) & filters.private)
async def group_stats(client: Client, message):
    """Handle the /gpstats command to display paginated statistics for all VCF groups."""
    logger.debug(f"Handling /gpstats for admin {message.from_user.id}")
    try:
        # Fetch all groups from database
        groups = get_all_groups()
        group_list = list(groups)  # Convert cursor to list
        if not group_list:
            await message.reply_text("❌ No groups found in the database.")
            logger.warning("No groups available for stats")
            return

        # Initialize pagination state
        admin_id = message.from_user.id
        pagination_state[admin_id] = {"page": 0, "groups": group_list}

        # Get first page
        message_text, reply_markup = get_paginated_groups(group_list, 0)
        await message.reply_text(message_text, reply_markup=reply_markup)
        logger.info(f"Displayed group stats page 1 for admin {admin_id}")
    except Exception as e:
        await message.reply_text("❌ Error fetching group stats. Please try again.")
        logger.error(f"Error fetching group stats for admin {admin_id}: {e}", exc_info=True)

@Client.on_callback_query(filters.regex(r"^gpstats_(next|back)_(\d+)$") & filters.user(ADMIN_IDS))
async def group_stats_navigation(client: Client, callback_query):
    """Handle pagination navigation for group stats."""
    logger.debug(f"Handling group stats navigation for admin {callback_query.from_user.id}")
    try:
        admin_id = callback_query.from_user.id
        if admin_id not in pagination_state:
            await callback_query.answer("Session expired. Use /gpstats to start again.", show_alert=True)
            return

        action, page_str = callback_query.data.split("_")[1:]
        current_page = int(page_str)
        group_list = pagination_state[admin_id]["groups"]

        # Update page based on action
        if action == "next":
            new_page = current_page + 1
        elif action == "back":
            new_page = current_page - 1
        else:
            await callback_query.answer("Invalid action.")
            return

        # Update pagination state
        pagination_state[admin_id]["page"] = new_page

        # Get paginated content
        message_text, reply_markup = get_paginated_groups(group_list, new_page)
        await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
        await callback_query.answer()
        logger.info(f"Navigated to group stats page {new_page + 1} for admin {admin_id}")
    except Exception as e:
        await callback_query.answer("Error navigating stats. Try /gpstats again.", show_alert=True)
        logger.error(f"Error navigating group stats for admin {admin_id}: {e}", exc_info=True)
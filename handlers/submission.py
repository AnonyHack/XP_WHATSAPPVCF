import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.groups import get_active_groups_by_limit, get_group, increment_group_users, get_all_groups
from database.users import add_user
from handlers.notifications import handle_group_full

# Setup logging
logger = logging.getLogger(__name__)

# In-memory state to track users waiting to submit name/number
user_states = {}  # Format: {user_id: {"group_id": str, "handler": MessageHandler}}

@Client.on_callback_query(filters.regex("^submit_numbers$"))
async def handle_submit_numbers(client: Client, callback_query):
    """Display the 'Submit Numbers' page with group selection buttons."""
    logger.debug(f"Handling submit_numbers callback for user {callback_query.from_user.id}")
    try:
        # Fetch all groups from database
        groups = get_all_groups()
        group_list = list(groups)
        if not group_list:
            await callback_query.message.edit_text(
                "❌ No groups available for submission.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
                ])
            )
            logger.warning("No groups available for submit_numbers")
            return

        # Build buttons dynamically
        buttons = [
            [InlineKeyboardButton(f"👥 {group['limit']} VCF GROUP 👥", callback_data=f"select_group_{group['limit']}")]
            for group in group_list
        ]
        buttons.append([InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")])
        reply_markup = InlineKeyboardMarkup(buttons)

        await callback_query.message.edit_text(
            "📲 Choose a VCF group below to submit your number and join:",
            reply_markup=reply_markup
        )
        logger.info(f"Displayed {len(group_list)} group buttons for user {callback_query.from_user.id}")
    except Exception as e:
        await callback_query.message.edit_text(
            "❌ Error loading groups. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        logger.error(f"Error in submit_numbers for user {callback_query.from_user.id}: {e}", exc_info=True)

@Client.on_callback_query(filters.regex("^select_group_(\d+)$"))
async def handle_group_select(client: Client, callback_query):
    """Handle group selection and show group information."""
    limit = int(callback_query.data.split("_")[-1])
    try:
        active_groups = get_active_groups_by_limit(limit)
        if not active_groups:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("⏮️ Back To Select Group", callback_data="submit_numbers")],
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
            await callback_query.message.edit_text(
                f"❌ Failed to create or fetch active {limit} groups. Please try again later.",
                reply_markup=markup
            )
            logger.error(f"Failed to get or create active {limit} groups for user {callback_query.from_user.id}")
            return

        # Use the first active group
        group_id = active_groups[0]["group_id"]
        await handle_group_info(client, callback_query, group_id)
    except Exception as e:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏮️ Back To Select Group", callback_data="submit_numbers")],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
        ])
        await callback_query.message.edit_text(
            "❌ An error occurred. Please try again later.",
            reply_markup=markup
        )
        logger.error(f"Error in group selection for limit {limit} by user {callback_query.from_user.id}: {e}")

async def handle_group_info(client: Client, callback_query, group_id: str):
    """Display group information page with submission and navigation options."""
    group = get_group(group_id)
    if not group:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏮️ Back To Select Group", callback_data="submit_numbers")],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
        ])
        await callback_query.message.edit_text(
            "Group not found.",
            reply_markup=markup
        )
        logger.info(f"Group {group_id} not found for user {callback_query.from_user.id}")
        return

    if group["status"] == "full":
        await handle_group_full(client, callback_query)
        return

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Submit My Number", callback_data=f"submit_my_number_{group_id}")],
        [InlineKeyboardButton("⏮️ Back To Select Group", callback_data="submit_numbers")],
        [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
    ])
    await callback_query.message.edit_text(
        f"📦 Group: {group['limit']} Users VCF\n"
        f"👥 Current Members: {group['current_users']}/{group['limit']}\n"
        f"📅 Status: {group['status'].capitalize()}\n\n"
        "ℹ️ Once this group is full, the admin will approve it and share the VCF file on our download channel.",
        reply_markup=markup
    )
    logger.info(f"Displayed group {group_id} info for user {callback_query.from_user.id}")

@Client.on_callback_query(filters.regex("^submit_my_number_(.+)$"))
async def handle_submit_my_number(client: Client, callback_query):
    """Prompt user to submit name and number in a specific format."""
    group_id = callback_query.data.split("_", 3)[-1]
    user_id = callback_query.from_user.id

    # Check if group is still active
    group = get_group(group_id)
    if not group or group["status"] == "full":
        await handle_group_full(client, callback_query)
        return

    # Store user state
    async def submission_callback(client: Client, message):
        if message.from_user.id == user_id:
            await handle_submission(client, message, group_id)

    submission_handler = MessageHandler(submission_callback, filters.text & filters.user(user_id) & filters.private)
    user_states[user_id] = {"group_id": group_id, "handler": submission_handler}
    client.add_handler(submission_handler)

    await callback_query.message.edit_text(
        "📝 Please send your name and phone number in this format:\n"
        "Name: John Doe\n"
        "Number: +256787xxxxxx",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="back_to_home")]
        ])
    )
    logger.info(f"Prompted submission for group {group_id} by user {user_id}")

async def handle_submission(client: Client, message, group_id: str):
    """Handle user submission of name and number, show confirmation UI."""
    user_id = message.from_user.id
    # Check if user is in submission state
    if user_id not in user_states or user_states[user_id]["group_id"] != group_id:
        await message.reply_text("Session expired. Please start again by selecting a group.")
        logger.info(f"Session expired for user {user_id}")
        return

    # Parse the message text
    lines = message.text.split("\n")
    if len(lines) != 2 or not lines[0].startswith("Name: ") or not lines[1].startswith("Number: "):
        await message.reply_text(
            "Invalid format. Please send in the format:\nName: John Doe\nNumber: +256787xxxxxx",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="back_to_home")]
            ])
        )
        logger.info(f"Invalid submission format by user {user_id}")
        return

    name = lines[0].replace("Name: ", "").strip()
    number = lines[1].replace("Number: ", "").strip()

    # Remove handler
    handler = user_states[user_id]["handler"]
    client.remove_handler(handler)

    # Clear user state
    user_states.pop(user_id, None)

    # Show confirmation UI
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_submission_{group_id}__{name}__{number}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="back_to_home")]
    ])
    await message.reply_text(
        f"✅ You submitted:\nName: {name}\nNumber: {number}\nConfirm submission?",
        reply_markup=markup
    )
    logger.info(f"Displayed confirmation for user {user_id} in group {group_id}")

@Client.on_callback_query(filters.regex(r"^confirm_submission_(.+?)__(.+?)__(.+)$"))
async def handle_confirm_submission(client: Client, callback_query):
    """Handle confirmation of submission and save to database."""
    # Parse callback data
    import re
    match = re.match(r"^confirm_submission_(.+?)__(.+?)__(.+)$", callback_query.data)
    if not match:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Try Again", callback_data="submit_numbers")],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
        ])
        await callback_query.message.edit_text(
            "❌ Invalid submission data. Please try again.",
            reply_markup=markup
        )
        logger.error(f"Invalid callback data for user {callback_query.from_user.id}: {callback_query.data}")
        return

    group_id, name, number = match.groups()
    user_id = callback_query.from_user.id

    # Save user submission
    try:
        if not add_user(user_id, name, number, group_id):
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Try Again", callback_data="submit_numbers")],
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
            await callback_query.message.edit_text(
                "❌ Failed to save your submission. Please try again.",
                reply_markup=markup
            )
            logger.error(f"Failed to save submission for user {user_id} in group {group_id}")
            return

        # Increment group user count and check if group is full
        if not increment_group_users(group_id):
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Try Again", callback_data="submit_numbers")],
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
            await callback_query.message.edit_text(
                "❌ Failed to update group. Please try again.",
                reply_markup=markup
            )
            logger.error(f"Failed to increment users for group {group_id} for user {user_id}")
            return

        group = get_group(group_id)
        if group and group["status"] == "full":
            await handle_group_full(client, callback_query)
            return

        await callback_query.message.edit_text(
            "✅ Your details have been saved successfully!\n"
            "We'll notify you once this group's VCF file is ready.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        logger.info(f"Confirmed submission for user {user_id} in group {group_id}")
    except Exception as e:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Try Again", callback_data="submit_numbers")],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
        ])
        await callback_query.message.edit_text(
            "❌ An error occurred. Please try again later.",
            reply_markup=markup
        )
        logger.error(f"Error confirming submission for user {user_id} in group {group_id}: {e}")

@Client.on_callback_query(filters.regex(r"^back_to_home$"))
async def handle_back_to_home(client: Client, callback_query):
    """Navigate back to the home page."""
    user_id = callback_query.from_user.id
    logger.debug(f"Received back_to_home callback for user {user_id}")
    try:
        # Clear user state and remove handler if exists
        if user_id in user_states:
            handler = user_states[user_id].get("handler")
            if handler:
                client.remove_handler(handler)
                logger.debug(f"Removed message handler for user {user_id}")
            user_states.pop(user_id, None)
            logger.debug(f"Cleared user state for user {user_id}")

        # Send a new message to simulate /start
        from config import WELCOME_MESSAGE, WELCOME_IMAGE
        from database.connection import get_db
        from database.users import register_user, update_user_subscription_status
        from handlers.force_join import check_subscription, prompt_subscription

        # Register user in the database
        if not register_user(user_id):
            logger.error(f"Failed to register user {user_id} on back_to_home")
            await callback_query.message.edit_text(
                "❌ An error occurred while returning to home. Please try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Try Again", callback_data="back_to_home")]
                ])
            )
            return

        # Check subscription status
        db = get_db()
        user = db.users.find_one({"user_id": user_id})
        if not user or not user.get("subscribed", False):
            logger.debug(f"User {user_id} not subscribed, checking channel membership")
            if await check_subscription(client, user_id):
                update_user_subscription_status(user_id, True)
                logger.info(f"User {user_id} was already subscribed, updated status")
            else:
                await prompt_subscription(client, callback_query.message, user_id)
                return

        # Create inline keyboard for home page with 2 columns
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
                    chat_id=callback_query.message.chat.id,
                    photo=WELCOME_IMAGE,
                    caption=WELCOME_MESSAGE,
                    reply_markup=markup
                )
                logger.info(f"Sent back_to_home photo to user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send photo for user {user_id}: {e}")
                await client.send_message(
                    chat_id=callback_query.message.chat.id,
                    text=WELCOME_MESSAGE,
                    reply_markup=markup
                )
                logger.info(f"Sent back_to_home message (fallback) to user {user_id}")
        else:
            await client.send_message(
                chat_id=callback_query.message.chat.id,
                text=WELCOME_MESSAGE,
                reply_markup=markup
            )
            logger.info(f"Sent back_to_home message to user {user_id}")
        await callback_query.message.delete()  # Delete the previous message
        logger.info(f"Navigated back to home for user {user_id}")
    except Exception as e:
        logger.error(f"Error navigating back to home for user {user_id}: {e}")
        await callback_query.message.edit_text(
            "❌ An error occurred while returning to home. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Try Again", callback_data="back_to_home")]
            ])
        )

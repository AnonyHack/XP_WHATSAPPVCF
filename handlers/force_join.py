import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import REQUIRED_CHANNELS

# Setup logging
logger = logging.getLogger(__name__)

async def check_subscription(client: Client, user_id: int) -> bool:
    """Check if a user is subscribed to all required channels."""
    for channel in REQUIRED_CHANNELS:
        try:
            await client.get_chat_member(chat_id=channel["chat_id"], user_id=user_id)
            logger.debug(f"User {user_id} is subscribed to {channel['name']} ({channel['chat_id']})")
        except UserNotParticipant:
            logger.info(f"User {user_id} is not subscribed to {channel['name']} ({channel['chat_id']})")
            return False
        except Exception as e:
            logger.error(f"Error checking subscription for user {user_id} in {channel['chat_id']}: {e}")
            return False
    logger.info(f"User {user_id} is subscribed to all required channels")
    return True


async def prompt_subscription(client: Client, message, user_id: int):
    """Prompt user to join required channels."""
    buttons = [
        [InlineKeyboardButton(f"Join {channel['name']}", url=channel["url"])]
        for channel in REQUIRED_CHANNELS
    ]
    buttons.append([InlineKeyboardButton("✅ Check Subscription", callback_data="check_subscription")])
    prompt_msg = await message.reply_text(   # 🆕 store the message
        "📢 Please join our channel(s) to use the bot:\n\n"
        + "\n".join([f"- {channel['name']}" for channel in REQUIRED_CHANNELS])
        + "\n\nClick the button(s) below to join, then press 'Check Subscription'.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    logger.info(f"Prompted user {user_id} to join required channels")
    return prompt_msg  # 🆕 return it so it can later be deleted


@Client.on_callback_query(filters.regex(r"^check_subscription$"))
async def handle_check_subscription(client: Client, callback_query):
    """Handle the 'Check Subscription' button and redirect to home if subscribed."""
    user_id = callback_query.from_user.id
    logger.debug(f"Checking subscription for user {user_id} on callback")

    try:
        from database.users import update_user_subscription_status

        if await check_subscription(client, user_id):
            update_user_subscription_status(user_id, True)
            from handlers.start import handle_start

            # 🆕 Delete the "join required channels" message before redirecting
            try:
                await callback_query.message.delete()
                logger.debug(f"Deleted force-join message for user {user_id}")
            except Exception as e:
                logger.warning(f"Couldn't delete force-join message for user {user_id}: {e}")

            # Create minimal mock message
            mock_message = type('MockMessage', (), {})()
            mock_message.chat = callback_query.message.chat
            mock_message.from_user = callback_query.from_user

            try:
                await handle_start(client, mock_message)
                logger.info(f"User {user_id} passed subscription check, redirected to home")
            except Exception as e:
                logger.error(f"Failed to redirect to start for user {user_id}: {e}", exc_info=True)
                msg = await callback_query.message.reply_text(
                    "✅ Subscription verified! Please send /start to continue.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Start", callback_data="retry_start")]
                    ])
                )
                # 🆕 Auto-delete success message after a few seconds
                await asyncio.sleep(5)
                await msg.delete()

        else:
            await callback_query.message.edit_text(
                "❌ You haven't joined all required channels.\n\n"
                + "\n".join([f"- {channel['name']}" for channel in REQUIRED_CHANNELS])
                + "\n\nPlease join and try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Join {channel['name']}", url=channel["url"])]
                    for channel in REQUIRED_CHANNELS
                ] + [[InlineKeyboardButton("✅ Check Subscription", callback_data="check_subscription")]])
            )
            logger.info(f"User {user_id} failed subscription check")

    except Exception as e:
        await callback_query.message.edit_text(
            "❌ Error checking subscription. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Try Again", callback_data="check_subscription")]
            ])
        )
        logger.error(f"Error in check_subscription for user {user_id}: {e}", exc_info=True)


@Client.on_callback_query(filters.regex(r"^retry_start$"))
async def handle_retry_start(client: Client, callback_query):
    """Handle retry start callback if redirect fails."""
    user_id = callback_query.from_user.id
    logger.debug(f"Handling retry_start for user {user_id}")

    try:
        from handlers.start import handle_start

        # 🆕 delete the retry message too
        try:
            await callback_query.message.delete()
        except Exception:
            pass

        mock_message = type('MockMessage', (), {})()
        mock_message.chat = callback_query.message.chat
        mock_message.from_user = callback_query.from_user
        await handle_start(client, mock_message)
        logger.info(f"Processed retry_start for user {user_id}")
    except Exception as e:
        await callback_query.message.edit_text(
            "❌ Error starting bot. Please send /start manually."
        )
        logger.error(f"Error in retry_start for user {user_id}: {e}", exc_info=True)

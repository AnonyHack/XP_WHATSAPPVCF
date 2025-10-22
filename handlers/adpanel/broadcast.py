import logging
import time
import datetime
from pyrogram import Client, filters
from pyrogram.errors import UserIsBlocked, PeerIdInvalid
from config import ADMIN_IDS
from database.users import get_all_users, total_users_count

# Setup logging
logger = logging.getLogger(__name__)

# Temporary storage for broadcast state
broadcast_state = {}

async def broadcast_messages(client: Client, user_id: int, message) -> tuple[bool, str]:
    """Send a broadcast message to a user and return status."""
    try:
        await message.copy(chat_id=user_id)
        logger.debug(f"Successfully broadcasted to user {user_id}")
        return True, "Success"
    except UserIsBlocked:
        logger.info(f"User {user_id} has blocked the bot")
        return False, "Blocked"
    except PeerIdInvalid:
        logger.info(f"User {user_id} has deleted their account or is invalid")
        return False, "Deleted"
    except Exception as e:
        logger.error(f"Failed to broadcast to user {user_id}: {e}")
        return False, "Error"

@Client.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS) & filters.private)
async def pm_broadcast(client: Client, message):
    """Handle the /broadcast command to send messages to all users."""
    logger.debug(f"Handling /broadcast for admin {message.from_user.id}")
    try:
        admin_id = message.from_user.id
        # Store the admin's state to expect a broadcast message
        broadcast_state[admin_id] = {"awaiting_message": True}

        # Prompt admin for the broadcast message
        await message.reply_text(
            "📢 Please send the broadcast message (text, photo, etc.).",
            quote=True
        )
        logger.info(f"Prompted admin {admin_id} for broadcast message")
    except Exception as e:
        await message.reply_text("❌ Error initiating broadcast. Please try again.")
        logger.error(f"Error initiating broadcast for admin {admin_id}: {e}", exc_info=True)

@Client.on_message(filters.user(ADMIN_IDS) & filters.private)
async def handle_broadcast_message(client: Client, message):
    """Handle the broadcast message sent by the admin."""
    admin_id = message.from_user.id
    if admin_id not in broadcast_state or not broadcast_state[admin_id].get("awaiting_message"):
        return  # Ignore if not expecting a broadcast message

    try:
        # Clear the broadcast state for this admin
        del broadcast_state[admin_id]
        logger.info(f"Received broadcast message from admin {admin_id}")

        # Get all users from database
        users = get_all_users()
        total_users = total_users_count()
        if total_users == 0:
            await message.reply_text("❌ No users found in the database.")
            logger.warning("No users available for broadcast")
            return

        sts = await message.reply_text("Broadcasting your message...")

        # Track broadcast progress
        start_time = time.time()
        done = 0
        blocked = 0
        deleted = 0
        failed = 0
        success = 0

        for user in users:
            if 'user_id' in user:
                pti, sh = await broadcast_messages(client, int(user['user_id']), message)
                if pti:
                    success += 1
                elif sh == "Blocked":
                    blocked += 1
                elif sh == "Deleted":
                    deleted += 1
                elif sh == "Error":
                    failed += 1
                done += 1
                if done % 20==-0:
                    await sts.edit_text(
                        f"Broadcast in progress:\n\n"
                        f"Total Users: {total_users}\n"
                        f"Completed: {done} / {total_users}\n"
                        f"Success: {success}\n"
                        f"Blocked: {blocked}\n"
                        f"Deleted: {deleted}"
                    )
                    logger.debug(f"Broadcast progress: {done}/{total_users}")
            else:
                done += 1
                failed += 1
                logger.warning(f"User document missing 'user_id': {user}")
                if done % 20 == 0:
                    await sts.edit_text(
                        f"Broadcast in progress:\n\n"
                        f"Total Users: {total_users}\n"
                        f"Completed: {done} / {total_users}\n"
                        f"Success: {success}\n"
                        f"Blocked: {blocked}\n"
                        f"Deleted: {deleted}"
                    )

        # Calculate time taken
        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await sts.edit_text(
            f"Broadcast Completed:\n"
            f"Completed in {time_taken} seconds.\n\n"
            f"Total Users: {total_users}\n"
            f"Completed: {done} / {total_users}\n"
            f"Success: {success}\n"
            f"Blocked: {blocked}\n"
            f"Deleted: {deleted}"
        )
        logger.info(f"Broadcast completed for admin {admin_id}: Success={success}, Blocked={blocked}, Deleted={deleted}, Failed={failed}")
    except Exception as e:
        # Clear the broadcast state in case of error
        if admin_id in broadcast_state:
            del broadcast_state[admin_id]
        await message.reply_text("❌ Error during broadcast. Please try again.")
        logger.error(f"Broadcast error for admin {admin_id}: {e}", exc_info=True)

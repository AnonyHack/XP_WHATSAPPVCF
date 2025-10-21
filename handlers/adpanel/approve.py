import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_IDS, DOWNLOAD_CHANNEL
from database.groups import get_group, update_group_status
from database.connection import get_db
from handlers.notifications import handle_vcf_ready
from utils.vcf_generator import generate_vcf
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    return user_id in ADMIN_IDS

@Client.on_message(filters.command("approve") & filters.private)
async def handle_approve(client: Client, message):
    """Approve a group, generate VCF with watermark, upload to channel, and notify users."""
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply_text("🚫 You are not authorized to use this command.")
        logger.warning(f"Unauthorized /approve attempt by user {user_id}")
        return

    # Extract group_id from command
    args = message.text.split()
    if len(args) != 2:
        await message.reply_text(
            "Usage: /approve <group_id>\nExample: /approve ID-XP100GROUP",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        logger.info(f"Invalid /approve command by user {user_id}: {message.text}")
        return

    group_id = args[1]
    
    try:
        # Find the group by group_id
        group = get_group(group_id)
        if not group:
            await message.reply_text(
                f"❌ Group {group_id} not found.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
                ])
            )
            logger.info(f"Group {group_id} not found for /approve by user {user_id}")
            return

        if group["status"] == "approved":
            await message.reply_text(
                f"Group {group_id} is already approved.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
                ])
            )
            logger.info(f"Group {group_id} already approved for user {user_id}")
            return

        # 1️⃣ Collect all submissions in that group
        db = get_db()
        users = list(db.users.find({"group_id": group_id, "name": {"$exists": True}}))
        if not users:
            await message.reply_text(
                f"❌ No users found in group {group_id}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
                ])
            )
            logger.info(f"No users found in group {group_id} for /approve by user {user_id}")
            return

        total_contacts = len(users)
        logger.info(f"Collected {total_contacts} submissions from group {group_id}")

        # 2️⃣ & 3️⃣ Generate VCF file
        vcf_path = generate_vcf(group_id)
        if not vcf_path:
            await message.reply_text(
                f"❌ Failed to generate VCF file for group {group_id}.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
                ])
            )
            logger.error(f"Failed to generate VCF for group {group_id} for user {user_id}")
            return

        logger.info(f"Generated VCF file for group {group_id}")

        # 4️⃣ Upload file to download channel with proper caption
        current_date = datetime.now().strftime("%b %d, %Y")
        caption = (
            f"📁 Group: {group_id} VCF\n"
            f"👥 Total Contacts: {total_contacts}\n"
            f"📅 Generated on: {current_date}\n"
            f"⚠️ Warning: Do NOT download this file if you didn't submit to this group."
        )

        try:
            # Check if DOWNLOAD_CHANNEL is a dictionary (old format) or direct channel ID
            if isinstance(DOWNLOAD_CHANNEL, dict):
                # Old format: {"chat_id": -100xxx, "url": "https://t.me/..."}
                chat_id = DOWNLOAD_CHANNEL["chat_id"]
                channel_url = DOWNLOAD_CHANNEL["url"]
            else:
                # New format: direct channel ID/username
                chat_id = DOWNLOAD_CHANNEL
                # Get channel info to construct URL
                channel = await client.get_chat(chat_id)
                channel_username = channel.username
                channel_url = f"https://t.me/{channel_username}"

            # Send VCF file to download channel
            sent_message = await client.send_document(
                chat_id=chat_id,
                document=vcf_path,
                caption=caption,
                file_name=f"VCF_Group_{group_id}.vcf"
            )
            
            # Get the message link for the download button
            message_id = sent_message.id
            if isinstance(DOWNLOAD_CHANNEL, dict):
                # For old format, we already have the base URL
                download_url = f"{channel_url}/{message_id}"
            else:
                # For new format, construct the URL
                download_url = f"https://t.me/{channel_username}/{message_id}"
            
            logger.info(f"Uploaded VCF file for group {group_id} to download channel")

        except Exception as e:
            await message.reply_text(
                f"❌ Failed to upload VCF file to channel: {e}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
                ])
            )
            logger.error(f"Failed to upload VCF for group {group_id} to channel: {e}")
            return

        # 5️⃣ Notify all users in that group
        notified_users = 0
        for user in users:
            try:
                await client.send_message(
                    chat_id=user["user_id"],
                    text=(
                        "✅ Your group's VCF file is ready!\n"
                        "📥 Download it from our channel below 👇"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📥 Download VCF File", url=download_url)]
                    ])
                )
                notified_users += 1
                logger.debug(f"Notified user {user['user_id']} about VCF ready for group {group_id}")
                
            except Exception as e:
                logger.error(f"Failed to notify user {user['user_id']} for group {group_id}: {e}")

        # Update group status to approved
        if not update_group_status(group_id, "approved"):
            logger.warning(f"Failed to update group {group_id} status to approved, but process completed")

        # Reset the group for reuse
        db.users.delete_many({"group_id": group_id})
        db.groups.update_one(
            {"group_id": group_id},
            {"$set": {"current_users": 0, "status": "active", "updated_at": datetime.now()}}
        )
        logger.info(f"Reset group {group_id} after approval")

        # Send final confirmation to admin with download URL in buttons
        await message.reply_text(
            f"✅ Approval Process Completed!\n\n"
            f"📊 Group: {group_id}\n"
            f"👥 Notified Users: {notified_users}/{total_contacts}\n"
            f"📁 VCF File: Uploaded to channel",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Download VCF File", url=download_url)],
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        
        logger.info(f"Approved group {group_id}: {notified_users}/{total_contacts} users notified, VCF uploaded")

    except Exception as e:
        await message.reply_text(
            "❌ An error occurred while approving the group. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        logger.error(f"Error approving group {group_id} for user {user_id}: {e}", exc_info=True)
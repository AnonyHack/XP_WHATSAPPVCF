import logging
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import DOWNLOAD_CHANNEL, SUPPORT_GROUP_URL, SOURCE_CODE_URL, BOT_NAME, BOT_USERNAME, OWNER_USERNAME, TUTORIAL_VIDEO_URL
from database.users import get_user_submissions
from database.groups import get_group

# Setup logging
logger = logging.getLogger(__name__)

@Client.on_callback_query(filters.regex(r"^my_submissions$"))
async def handle_my_submissions(client: Client, callback_query):
    """Display the user's submitted groups."""
    user_id = callback_query.from_user.id
    try:
        submissions = get_user_submissions(user_id)
        
        if not submissions:
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                    InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
                ]
            ])
            await callback_query.message.edit_text(
                "You haven't submitted to any groups yet.\nSubmit your number to join a VCF group!",
                reply_markup=markup
            )
            logger.info(f"No submissions found for user {user_id}")
            return

        message = "📁 Your Submissions:\n\n"
        for submission in submissions:
            group_id = submission["group_id"]
            limit = submission["limit"]
            status = submission["status"]
            current_users = submission["current_users"]
            status_text = "✅ Approved" if status == "approved" else "⏳ Full, Awaiting Approval" if status == "full" else "📥 Active"
            message += f"Group: {limit} Users VCF\nStatus: {status_text}\nMembers: {current_users}/{limit}\n\n"

        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📤 Submit to Another Group", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(message, reply_markup=markup)
        logger.info(f"Displayed {len(submissions)} submissions for user {user_id}")
    except Exception as e:
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            "❌ An error occurred while fetching your submissions. Please try again.",
            reply_markup=markup
        )
        logger.error(f"Error fetching submissions for user {user_id}: {e}")

@Client.on_callback_query(filters.regex(r"^group_full_(.+)$"))
async def handle_group_full(client: Client, callback_query):
    """Notify user when a group is full."""
    group_id = callback_query.data.split("_", 2)[-1]
    try:
        group = get_group(group_id)
        
        if not group or group["status"] != "full":
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                    InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
                ]
            ])
            await callback_query.message.edit_text(
                "Group not found or not full.",
                reply_markup=markup
            )
            logger.info(f"Group {group_id} not full or not found for user {callback_query.from_user.id}")
            return

        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📤 Submit to Another Group", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            f"❌ Group {group['limit']} Users VCF is full ({group['current_users']}/{group['limit']}).\n"
            f"⏳ Awaiting admin approval. You'll be notified when the VCF file is ready in {DOWNLOAD_CHANNEL['name']}.",
            reply_markup=markup
        )
        logger.info(f"Notified user {callback_query.from_user.id} about full group {group_id}")
    except Exception as e:
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            "❌ An error occurred while checking group status. Please try again.",
            reply_markup=markup
        )
        logger.error(f"Error checking group full status for group {group_id} for user {callback_query.from_user.id}: {e}")

@Client.on_callback_query(filters.regex(r"^vcf_ready_(.+)$"))
async def handle_vcf_ready(client: Client, callback_query):
    """Notify user when the VCF file is ready."""
    group_id = callback_query.data.split("_", 2)[-1]
    try:
        group = get_group(group_id)
        
        if not group or group["status"] != "approved":
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                    InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
                ]
            ])
            await callback_query.message.edit_text(
                "Group not found or VCF not ready.",
                reply_markup=markup
            )
            logger.info(f"Group {group_id} not approved or not found for user {callback_query.from_user.id}")
            return

        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📥 Download VCF", url=DOWNLOAD_CHANNEL["url"]),
                InlineKeyboardButton("📤 Submit to Another Group", callback_data="submit_numbers")
            ],
            [
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            f"🎉 The {group['limit']} Users VCF group is approved!\n"
            f"📥 Download the VCF file from {DOWNLOAD_CHANNEL['name']} now!",
            reply_markup=markup
        )
        logger.info(f"Notified user {callback_query.from_user.id} about VCF ready for group {group_id}")
    except Exception as e:
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            "❌ An error occurred while checking VCF status. Please try again.",
            reply_markup=markup
        )
        logger.error(f"Error checking VCF ready status for group {group_id} for user {callback_query.from_user.id}: {e}")

@Client.on_callback_query(filters.regex(r"^about_bot$"))
async def handle_about_bot(client: Client, callback_query):
    """Display the About Bot page."""
    try:
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👥 Support Group", url=SUPPORT_GROUP_URL),
                InlineKeyboardButton("⚙️ Source Code", url=SOURCE_CODE_URL)
            ],
            [
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            "<b>⍟───[ ᴍʏ ᴅᴇᴛᴀɪʟꜱ ]───⍟</b>\n\n"
            "<blockquote>"
            f"‣ ᴍʏ ɴᴀᴍᴇ : <a href=\"https://t.me/{BOT_USERNAME}\">{BOT_NAME}</a> 🔍\n"
            "‣ ᴍʏ ʙᴇsᴛ ғʀɪᴇɴᴅ : <a href=\"tg://settings\">ᴛʜɪs ᴘᴇʀsᴏɴ</a>\n"
            f"‣ ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href=\"https://t.me/{OWNER_USERNAME}\">ᴏᴡɴᴇʀ</a>\n"
            "‣ ʟɪʙʀᴀʀʏ : <a href=\"https://docs.pyrogram.org/\">ᴘʏʀᴏɢʀᴀᴍ</a>\n"
            "‣ ʟᴀɴɢᴜᴀɢᴇ : <a href=\"https://www.python.org/download/releases/3.0/\">ᴘʏᴛʜᴏɴ 3</a>\n"
            "‣ ᴅᴀᴛᴀʙᴀsᴇ : <a href=\"https://www.mongodb.com/\">ᴍᴏɴɢᴏ ᴅʙ</a>\n"
            "‣ ʙᴏᴛ sᴇʀᴠᴇʀ : <a href=\"https://heroku.com/\">ʜᴇʀᴏᴋᴜ</a>\n"
            "‣ ʙᴜɪʟᴅ sᴛᴀᴛᴜs : <a href=\"#\">ᴠ1.0 [sᴛᴀʙʟᴇ]</a>"
            "</blockquote>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Displayed about bot page for user {callback_query.from_user.id}")
    except Exception as e:
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            "❌ An error occurred while displaying the About page. Please try again.",
            reply_markup=markup
        )
        logger.error(f"Error displaying about bot page for user {callback_query.from_user.id}: {e}")

@Client.on_callback_query(filters.regex(r"^tutorial$"))
async def handle_tutorial(client: Client, callback_query):
    """Display the Tutorial page."""
    try:
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎥 Watch Tutorial", url=TUTORIAL_VIDEO_URL),
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers")
            ],
            [
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            "<b>⍟───[ ᴛᴜᴛᴏʀɪᴀʟ ]───⍟</b>\n\n"
            "<blockquote>"
            f"‣ sᴛᴇᴘ 1 : Click 'Add Number' to submit your WhatsApp number.\n"
            f"‣ sᴛᴇᴘ 2 : Join an active VCF group to share your number.\n"
            f"‣ sᴛᴇᴘ 3 : Wait for the group to be approved by admins.\n"
            f"‣ sᴛᴇᴘ 4 : Download the VCF file from <a href=\"{DOWNLOAD_CHANNEL['url']}\">{DOWNLOAD_CHANNEL['name']}</a>.\n"
            "‣ sᴛᴇᴘ 5 : Import the VCF to your contacts to boost your WhatsApp Status views!"
            "</blockquote>",
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Displayed tutorial page for user {callback_query.from_user.id}")
    except Exception as e:
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add Number", callback_data="submit_numbers"),
                InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")
            ]
        ])
        await callback_query.message.edit_text(
            "❌ An error occurred while displaying the Tutorial page. Please try again.",
            reply_markup=markup
        )
        logger.error(f"Error displaying tutorial page for user {callback_query.from_user.id}: {e}")

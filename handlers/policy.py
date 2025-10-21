import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from config import REQUIRED_CHANNELS, DOWNLOAD_CHANNEL

# Setup logging
logger = logging.getLogger(__name__)

@Client.on_message(filters.command("policy") & filters.private)
async def policy_command(client: Client, message):
    """Handle the /policy command to display terms and conditions."""
    logger.debug(f"Handling /policy for user {message.from_user.id}")
    try:
        main_channel_url = REQUIRED_CHANNELS[0]["url"]
        download_channel_url = DOWNLOAD_CHANNEL["url"]
        
        terms = (
            "<b>📜 Terms and Conditions for WhatsApp Status View Increaser Bot</b>\n\n"
            "<blockquote>1. <b>Purpose</b>: This bot allows you to increase your WhatsApp status views by joining VCF (Virtual Contact File) groups. By submitting your name and phone number, you agree to share your contact details with other group members to enhance status visibility.</blockquote>\n"
            "<blockquote>2. <b>Channel Membership</b>: You must join our required channels to use the bot. Failure to remain subscribed may restrict access to features. See buttons below for channels.</blockquote>\n"
            "<blockquote>3. <b>Accurate Submissions</b>: Provide accurate and valid name and phone number details in the requested format. Submissions with incorrect or fraudulent information may be rejected.</blockquote>\n"
            "<blockquote>4. <b>Data Usage</b>: Your submitted phone number and name are stored temporarily in our database and included in a VCF file when the group is full. After the VCF file is generated and approved (typically within 24 hours), your data is automatically deleted from our database.</blockquote>\n"
            "<blockquote>5. <b>Prohibited Actions</b>: Do not use the bot for spam, harassment, or any illegal activities. Do not download VCF files for groups you did not join, as this violates user privacy.</blockquote>\n"
            "<blockquote>6. <b>Liability</b>: The bot is not responsible for how other users utilize the shared VCF files. Use the bot at your own risk. We do not guarantee specific increases in status views.</blockquote>\n"
            "<blockquote>7. <b>Changes to Terms</b>: These terms may be updated. Continued use of the bot implies acceptance of the updated terms.</blockquote>\n\n"
            f"By using this bot, you agree to these terms. For questions, contact our support team via the main channel below."
        )
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Main Channel", url=main_channel_url)],
            [InlineKeyboardButton("📁 Download Channel", url=download_channel_url)],
            [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
        ])
        await message.reply_text(
            terms,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        logger.info(f"Displayed policy to user {message.from_user.id}")
    except Exception as e:
        await message.reply_text(
            "❌ Error displaying terms and conditions. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")]
            ])
        )
        logger.error(f"Error in /policy for user {message.from_user.id}: {e}", exc_info=True)
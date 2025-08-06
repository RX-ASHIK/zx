import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler
)
from datetime import datetime, timedelta
import asyncio

# Configuration
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
ADMIN_ID = 5989402185
CHANNEL_USERNAME = "EarningMasterbd24"  # Without @
CHANNEL_LINK = "https://t.me/EarningMasterbd24"
MINI_APP_LINK = "https://earningmaster244.blogspot.com/?m=1"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database simulation (in a real bot, use a proper database)
users_db = {}
pending_verification = set()

async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    # Check if user is admin
    if user_id == ADMIN_ID:
        await admin_panel(update, context)
        return
    
    # Store user info
    users_db[user_id] = {
        "name": user.full_name,
        "username": user.username,
        "join_date": datetime.now(),
        "verified": False
    }
    
    # Check channel membership
    is_member = await check_channel_membership(user_id, context)
    
    if not is_member:
        # Send join channel message
        keyboard = [
            [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("Verify Join", callback_data="verify_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(
            f"🌟 Welcome {user.mention_html()} to <b>Earning Master Bot</b>! 🌟\n\n"
            "To start using the bot, please join our official channel first:\n"
            f"👉 {CHANNEL_LINK}\n\n"
            "After joining, click the 'Verify Join' button below.",
            reply_markup=reply_markup
        )
        pending_verification.add(user_id)
    else:
        await send_welcome_message(update, user_id)

async def check_channel_membership(user_id: int, context: CallbackContext) -> bool:
    """Check if user is a member of the channel."""
    try:
        chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

async def verify_join_callback(update: Update, context: CallbackContext) -> None:
    """Handle the verify join button."""
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in pending_verification:
        await query.answer("You didn't ask to verify joining!")
        return
    
    await query.answer()
    
    is_member = await check_channel_membership(user_id, context)
    
    if is_member:
        pending_verification.remove(user_id)
        users_db[user_id]["verified"] = True
        await send_welcome_message(update, user_id)
    else:
        await query.edit_message_text(
            "❌ You haven't joined our channel yet!\n\n"
            f"Please join {CHANNEL_LINK} and try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("Verify Join", callback_data="verify_join")]
            ])
        )

async def send_welcome_message(update: Update, user_id: int) -> None:
    """Send the welcome message with mini app link."""
    user_data = users_db.get(user_id, {})
    
    # Determine if the update is from callback or message
    if update.callback_query:
        message = update.callback_query.message
        edit = True
    else:
        message = update.message
        edit = False
    
    welcome_text = (
        f"🎉 Welcome <b>{user_data.get('name', '')}</b> to <b>Earning Master Bot</b>! 🎉\n\n"
        "💰 Start earning today with our mini app:\n"
        "👉 Click the button below to open directly\n\n"
        "💎 Complete tasks and earn rewards daily!\n"
        "🔔 You'll receive notifications with new opportunities."
    )
    
    # Create button that opens the mini app directly
    keyboard = [
        [InlineKeyboardButton("🚀 Open Mini App", web_app={"url": MINI_APP_LINK})],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit:
        await message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await message.reply_html(welcome_text, reply_markup=reply_markup)

async def admin_panel(update: Update, context: CallbackContext) -> None:
    """Show admin panel."""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("⚠️ You are not authorized to use this command!")
        return
    
    total_users = len(users_db)
    verified_users = sum(1 for user in users_db.values() if user.get("verified", False))
    
    keyboard = [
        [InlineKeyboardButton("📋 List All Users", callback_data="list_users")],
        [InlineKeyboardButton("📢 Send Broadcast", callback_data="send_broadcast")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(
        f"👑 <b>Admin Panel</b> 👑\n\n"
        f"📊 Total Users: {total_users}\n"
        f"✅ Verified Users: {verified_users}\n\n"
        "Select an option below:",
        reply_markup=reply_markup
    )

async def list_users_callback(update: Update, context: CallbackContext) -> None:
    """Handle list users button in admin panel."""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("⚠️ You are not authorized!")
        return
    
    if not users_db:
        await query.edit_message_text("No users in database yet.")
        return
    
    user_list = []
    for user_id, user_data in users_db.items():
        status = "✅" if user_data.get("verified", False) else "❌"
        user_list.append(
            f"{status} {user_data.get('name', 'Unknown')} (@{user_data.get('username', 'N/A')}) - {user_data.get('join_date', 'N/A')}"
        )
    
    user_list_text = "\n".join(user_list[:50])  # Show first 50 users to avoid message too long
    if len(users_db) > 50:
        user_list_text += f"\n\n...and {len(users_db) - 50} more users"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"👥 <b>User List</b> ({len(users_db)} total):\n\n{user_list_text}",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def send_notifications(context: CallbackContext) -> None:
    """Send notifications to all verified users every 5 minutes."""
    if not users_db:
        return
    
    notification_text = (
        "🔔 <b>Notification from Earning Master</b> 🔔\n\n"
        "🆕 New earning opportunities available!\n"
        "👉 Click the button below to check mini app\n\n"
        "💰 Complete tasks and earn rewards now!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Open Mini App Now", web_app={"url": MINI_APP_LINK})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for user_id, user_data in users_db.items():
        if user_data.get("verified", False):
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=notification_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error sending notification to {user_id}: {e}")

async def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message."""
    help_text = (
        "🆘 <b>Help Center</b> 🆘\n\n"
        "1. <b>Start Earning</b>: Click 'Open Mini App' button\n"
        "2. <b>Notifications</b>: You'll get updates every 5 minutes\n"
        "3. <b>Support</b>: Contact @EarningMasterSupport for help\n\n"
        "Remember to join our channel for updates!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Open Mini App", web_app={"url": MINI_APP_LINK})],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(help_text, reply_markup=reply_markup)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(verify_join_callback, pattern="^verify_join$"))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(list_users_callback, pattern="^list_users$"))
    application.add_handler(CallbackQueryHandler(send_welcome_message, pattern="^back_to_main$"))
    
    # Add notification job
    job_queue = application.job_queue
    job_queue.run_repeating(send_notifications, interval=300, first=300)  # Every 5 minutes

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

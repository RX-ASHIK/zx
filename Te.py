import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    WebAppInfo
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    JobQueue
)
import asyncio
from datetime import datetime
import random
import pytz

# Bot Configuration
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
ADMIN_ID = 5989402185
CHANNEL_LINK = "https://t.me/EarningMasterbd24"
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1"
NOTIFICATION_INTERVAL = 300  # 5 minutes
TIMEZONE = pytz.timezone('Asia/Dhaka')

# Professional Notification Messages
NOTIFICATION_MESSAGES = [
    "Time to boost your earnings!",
    "New earning opportunity available!",
    "Your daily session is ready!",
    "Increase your income now!",
    "Earning Master: Your time to shine!"
]

# User Data Management
user_data = {}
active_users = set()

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def send_clean_notification(context: ContextTypes.DEFAULT_TYPE):
    """Discreet notification system with button-only access"""
    try:
        for user_id in list(active_users):
            try:
                # Select random professional message
                clean_message = random.choice(NOTIFICATION_MESSAGES)
                
                # Create clean button (no visible link)
                button = InlineKeyboardButton(
                    text="🚀 Start Earning",
                    web_app=WebAppInfo(url=MINI_APP_URL)
                )
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=clean_message,
                    reply_markup=InlineKeyboardMarkup([[button]])
                )
                
                await asyncio.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Notification error for {user_id}: {e}")
                if "chat not found" in str(e).lower():
                    active_users.discard(user_id)
                    user_data.pop(user_id, None)
                    
    except Exception as e:
        logger.error(f"Notification system error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Store user with professional title
    if user_id not in user_data:
        user_data[user_id] = {
            'first_name': user.first_name,
            'join_date': datetime.now(TIMEZONE),
            'status': 'pending'
        }
    
    if user_id == ADMIN_ID:
        # Admin panel with clean interface
        buttons = [
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
            [InlineKeyboardButton("✉️ Broadcast", callback_data="admin_broadcast")]
        ]
        
        await update.message.reply_text(
            text="🛠️ *Admin Dashboard*\n\n"
                 "Manage your Earning Master system:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # Clean user onboarding
        buttons = [
            [InlineKeyboardButton("🔗 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Verify Join", callback_data="verify_join")]
        ]
        
        await update.message.reply_text(
            text="👋 *Welcome to Earning Master*\n\n"
                 "To access our platform:\n"
                 "1. Join our official channel\n"
                 "2. Verify your membership\n\n"
                 "You'll receive discreet earning reminders",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if query.data == "verify_join":
        user_data[user_id]['status'] = 'active'
        active_users.add(user_id)
        
        # Clean access button (no visible URL)
        button = InlineKeyboardButton(
            "💎 Access Earning Panel",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
        
        await query.edit_message_text(
            text="✅ *Verification Complete*\n\n"
                 "You now have full access to Earning Master.\n\n"
                 "You'll receive professional notifications.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[button]])
        )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⚠️ Unauthorized")
        return
    
    await query.answer()
    
    if query.data == "admin_stats":
        stats_text = (
            "📈 *System Statistics*\n\n"
            f"• Total Users: {len(user_data)}\n"
            f"• Active Users: {len(active_users)}\n"
            f"• Last Notification: {datetime.now(TIMEZONE).strftime('%I:%M %p')}"
        )
        
        await query.edit_message_text(
            text=stats_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
            ])
        )

def main():
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_verification, pattern="^verify_join$"))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_"))
    
    # Start notification system
    job_queue = application.job_queue
    job_queue.run_repeating(
        send_clean_notification,
        interval=NOTIFICATION_INTERVAL,
        first=10
    )
    
    # Run bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

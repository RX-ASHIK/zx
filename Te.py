import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from datetime import datetime, timedelta

# Bot configuration
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
ADMIN_ID = 5989402185  # Your admin ID
CHANNEL_USERNAME = "EarningMasterbd24"  # Channel username without @
CHANNEL_LINK = "https://t.me/EarningMasterbd24"
MINI_APP_LINK = "https://earningmaster244.blogspot.com/?m=1"
NOTIFICATION_INTERVAL = 300  # 5 minutes in seconds

# Store user data (in production, use a proper database)
user_data = {}
joined_users = set()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def send_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Send earning reminders to all users"""
    try:
        current_time = datetime.now()
        notification_count = 0
        
        for user_id, data in user_data.items():
            try:
                # Skip if user hasn't joined channel
                if not data.get('has_joined', False):
                    continue
                
                # Prepare the notification message
                message = (
                    "🔄 <b>Earning Reminder</b> 🔄\n\n"
                    "Don't forget to continue earning today!\n\n"
                    f"👉 <a href='{MINI_APP_LINK}'>Click here to start earning now</a>\n\n"
                    "The more you work, the more you earn! 💰"
                )
                
                # Send the notification
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                
                # Update last notified time
                user_data[user_id]['last_notified'] = current_time
                notification_count += 1
                
                # Small delay to avoid hitting rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to send notification to {user_id}: {e}")
                # Remove inactive users
                if "chat not found" in str(e).lower() or "user is deactivated" in str(e).lower():
                    user_data.pop(user_id, None)
                    joined_users.discard(user_id)
        
        # Log notification stats
        logger.info(f"Sent {notification_count} notifications at {current_time}")
        
    except Exception as e:
        logger.error(f"Error in notification job: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Store user info
    if user_id not in user_data:
        user_data[user_id] = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'has_joined': False,
            'last_notified': None
        }
    
    if user_id == ADMIN_ID:
        # Admin welcome message
        keyboard = [
            [InlineKeyboardButton("Admin Dashboard", callback_data="admin_dashboard")],
            [InlineKeyboardButton("Open Mini App", url=MINI_APP_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_html(
            f"👑 <b>Welcome Admin {user.first_name}!</b>\n\n"
            "You can access the admin dashboard to view bot statistics.",
            reply_markup=reply_markup
        )
    else:
        # Regular user welcome message with channel join requirement
        keyboard = [
            [InlineKeyboardButton("Join Our Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("I've Joined ✅", callback_data="check_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_html(
            f"👋 <b>Welcome {user.first_name}!</b>\n\n"
            "To use this bot, please join our channel first:\n"
            f"👉 {CHANNEL_LINK}\n\n"
            "After joining, click the 'I've Joined' button below to continue.\n\n"
            "💡 You'll receive regular reminders to help you earn more!",
            reply_markup=reply_markup
        )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if query.data == "check_join":
        user_data[user_id]['has_joined'] = True
        joined_users.add(user_id)
        
        keyboard = [
            [InlineKeyboardButton("Open Mini App Now", url=MINI_APP_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ Thank you for joining our channel!\n\n"
            "Now you can access our mini app:\n"
            f"{MINI_APP_LINK}\n\n"
            "⏰ You'll receive automatic reminders every 5 minutes to maximize your earnings!",
            reply_markup=reply_markup
        )
    
    elif query.data == "admin_dashboard" and user_id == ADMIN_ID:
        total_users = len(user_data)
        active_users = len(joined_users)
        
        await query.edit_message_text(
            f"📊 <b>Admin Dashboard</b>\n\n"
            f"👥 Total Users: {total_users}\n"
            f"✅ Active Users: {active_users}\n"
            f"❌ Pending Users: {total_users - active_users}\n\n"
            "Notifications are automatically sent every 5 minutes to all active users.",
            parse_mode="HTML"
        )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = " ".join(context.args)
    success = 0
    failed = 0
    
    for uid in user_data:
        try:
            await context.bot.send_message(uid, f"📢 Admin Broadcast:\n\n{message}")
            success += 1
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"Broadcast completed!\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}"
    )

def main():
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(button))
    
    # Schedule the notification job
    job_queue = application.job_queue
    job_queue.run_repeating(
        send_notifications,
        interval=NOTIFICATION_INTERVAL,
        first=10  # Start after 10 seconds
    )
    
    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()

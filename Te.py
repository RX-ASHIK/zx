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

# Bot configuration
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
ADMIN_ID = 5989402185
CHANNEL_LINK = "https://t.me/EarningMasterbd24"
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1"
NOTIFICATION_INTERVAL = 300  # 5 minutes in seconds
TIMEZONE = pytz.timezone('Asia/Dhaka')

# Premium notification messages
NOTIFICATION_MESSAGES = [
    "⏰ সময় এসেছে আয় বাড়ানোর! এখনই শুরু করুন:",
    "💰 আপনার আয়ের সুযোগ অপেক্ষা করছে! শুরু করতে ক্লিক করুন:",
    "🚀 আজকের আয়ের সেশন মিস করবেন না! শুরু করুন এখন:",
    "💎 আপনার আয়ের সম্ভাবনা বৃদ্ধি করুন! এখনই এক্সেস নিন:",
    "🤑 টাকা কামানোর সেরা সময় এখন! শুরু করতে ক্লিক করুন:"
]

# Store user data (in production use database)
user_data = {}
active_users = set()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def send_premium_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Send premium earning reminders to all active users"""
    try:
        current_time = datetime.now(TIMEZONE)
        notification_count = 0
        
        for user_id in list(active_users):
            try:
                # Select random premium message
                message = random.choice(NOTIFICATION_MESSAGES)
                
                # Create interactive button with WebApp
                keyboard = [
                    [InlineKeyboardButton(
                        text="📲 অ্যাপে যান এখনই", 
                        web_app=WebAppInfo(url=MINI_APP_URL)
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send the premium notification
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"{message}\n\n{MINI_APP_URL}",
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                notification_count += 1
                await asyncio.sleep(0.3)  # Rate limit protection
                
            except Exception as e:
                logger.error(f"Notification failed for {user_id}: {e}")
                if "chat not found" in str(e).lower():
                    active_users.discard(user_id)
                    user_data.pop(user_id, None)
        
        logger.info(f"✅ Sent {notification_count} premium notifications at {current_time.strftime('%I:%M %p')}")
        
    except Exception as e:
        logger.error(f"🚨 Notification system error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Initialize user data with Bengali language
    if user_id not in user_data:
        user_data[user_id] = {
            'name': user.full_name,
            'join_date': datetime.now(TIMEZONE).strftime("%d-%m-%Y %I:%M %p"),
            'status': 'pending'
        }
    
    if user_id == ADMIN_ID:
        # Premium admin panel
        keyboard = [
            [InlineKeyboardButton("📊 রিয়েল-টাইম স্ট্যাটস", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="admin_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo="https://i.imgur.com/JqYe5Zn.jpg",  # Premium banner image
            caption=f"🌟 <b>অ্যাডমিন ড্যাশবোর্ডে স্বাগতম</b> 🌟\n\n"
                   f"👑 আপনার বট বর্তমানে {len(active_users)} জন অ্যাক্টিভ ইউজার সেবা দিচ্ছে!\n\n"
                   "নিচের অপশনগুলো থেকে নির্বাচন করুন:",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    else:
        # Premium user onboarding
        keyboard = [
            [InlineKeyboardButton("🔗 চ্যানেল জয়েন করুন", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ জয়েন সম্পন্ন", callback_data="verify_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo="https://i.imgur.com/5XZwzP9.jpg",  # Welcome banner
            caption=f"🎉 <b>স্বাগতম {user.first_name}!</b> 🎉\n\n"
                   "আমাদের আয়ের প্ল্যাটফর্ম ব্যবহার করতে:\n"
                   "1. প্রথমে আমাদের চ্যানেল জয়েন করুন\n"
                   "2. তারপর নিচে 'জয়েন সম্পন্ন' বাটনে ক্লিক করুন\n\n"
                   f"🔗 চ্যানেল লিংক: {CHANNEL_LINK}",
            parse_mode="HTML",
            reply_markup=reply_markup
        )

async def handle_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if query.data == "verify_join":
        # In production, add actual channel verification here
        user_data[user_id]['status'] = 'active'
        active_users.add(user_id)
        
        # Premium WebApp integration
        keyboard = [
            [InlineKeyboardButton(
                text="🚀 আয় শুরু করুন", 
                web_app=WebAppInfo(url=MINI_APP_URL)
            ],
            [InlineKeyboardButton(
                text="📱 অ্যাপ ওপেন করুন", 
                url=MINI_APP_URL)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=f"🎊 <b>ধন্যবাদ {query.from_user.first_name}!</b> 🎊\n\n"
                   "✅ আপনি এখন আমাদের সম্পূর্ণ সিস্টেম এক্সেস করতে পারবেন!\n\n"
                   "আপনি প্রতি ৫ মিনিট পরপর আয়ের রিমাইন্ডার পাবেন।\n\n"
                   "নিচের বাটন ক্লিক করে এখনই আয় শুরু করুন:",
            parse_mode="HTML",
            reply_markup=reply_markup
        )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("⚠️ অননুমোদিত অ্যাক্সেস!")
        return
    
    await query.answer()
    
    if query.data == "admin_stats":
        # Premium admin statistics
        stats_text = (
            f"📈 <b>রিয়েল-টাইম স্ট্যাটিস্টিক্স</b>\n\n"
            f"👥 মোট ইউজার: {len(user_data)}\n"
            f"✅ অ্যাক্টিভ ইউজার: {len(active_users)}\n"
            f"⏳ পেন্ডিং ইউজার: {len(user_data) - len(active_users)}\n\n"
            f"🔄 শেষ নোটিফিকেশন: {datetime.now(TIMEZONE).strftime('%I:%M %p')}\n"
            f"🔔 পরবর্তী নোটিফিকেশন: {(datetime.now(TIMEZONE) + timedelta(seconds=NOTIFICATION_INTERVAL)).strftime('%I:%M %p')}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 রিফ্রেশ", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption=stats_text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    
    elif query.data == "admin_back":
        # Return to main admin menu
        keyboard = [
            [InlineKeyboardButton("📊 রিয়েল-টাইম স্ট্যাটস", callback_data="admin_stats")],
            [InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="admin_broadcast")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_caption(
            caption="🌟 <b>অ্যাডমিন ড্যাশবোর্ডে ফিরে আসার জন্য স্বাগতম</b> 🌟\n\n"
                   "নিচের অপশনগুলো থেকে নির্বাচন করুন:",
            parse_mode="HTML",
            reply_markup=reply_markup
        )

def main():
    # Create premium application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add premium handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_verification, pattern="^verify_join$"))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_"))
    
    # Start notification system
    job_queue = application.job_queue
    job_queue.run_repeating(
        send_premium_notifications,
        interval=NOTIFICATION_INTERVAL,
        first=15
    )
    
    # Run premium bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

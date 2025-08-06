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
import pytz

# কনফিগারেশন
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
ADMIN_ID = 5989402185
CHANNEL_USERNAME = "@EarningMasterbd24"  # @ চিহ্নসহ
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1"
NOTIFICATION_INTERVAL = 300  # 5 মিনিট
TIMEZONE = pytz.timezone('Asia/Dhaka')

# ডাটা স্টোরেজ
user_data = {}
active_users = set()

# লগিং
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """চেক করে ইউজার চ্যানেলে জয়েন করেছে কিনা"""
    try:
        member = await context.bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

async def send_welcome_message(user_id: int, context: ContextTypes.DEFAULT_TYPE, first_name: str):
    """সুন্দর ওয়েলকাম মেসেজ পাঠানো"""
    welcome_text = f"""
✨ *স্বাগতম {first_name}!* ✨

🎉 ইয়ার্নিং মাস্টার কমিউনিটিতে আপনাকে স্বাগতম!

💰 প্রতিদিন আয় করুন আমাদের বিশেষ সিস্টেমে

🚀 শুরু করতে নিচের বাটনে ক্লিক করুন:
"""
    
    keyboard = [
        [InlineKeyboardButton(
            "🚀 আয় শুরু করুন", 
            web_app=WebAppInfo(url=MINI_APP_URL)
        )]
    ]
    
    await context.bot.send_message(
        chat_id=user_id,
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # এডমিন চেক
    if user_id == ADMIN_ID:
        admin_text = f"""
👑 *অ্যাডমিন ড্যাশবোর্ড* 👑

স্বাগতম {user.first_name}!

📊 সক্রিয় ইউজার: {len(active_users)}
🕒 শেষ আপডেট: {datetime.now(TIMEZONE).strftime("%I:%M %p")}
"""
        keyboard = [
            [InlineKeyboardButton("📊 স্ট্যাটস", callback_data="admin_stats")],
            [InlineKeyboardButton("🚀 ওয়েবঅ্যাপ", web_app=WebAppInfo(url=MINI_APP_URL))]
        ]
        
        await update.message.reply_text(
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # চ্যানেল ভেরিফিকেশন
    if not await is_member(user_id, context):
        join_text = f"""
⚠️ *প্রিয় {user.first_name}* ⚠️

এই বট ব্যবহার করতে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন করতে হবে:

🔗 {CHANNEL_USERNAME}

✅ জয়েন করার পর নিচের বাটনে ক্লিক করুন:
"""
        keyboard = [
            [InlineKeyboardButton("🔗 চ্যানেল জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔄 ভেরিফাই করুন", callback_data="verify_join")]
        ]
        
        await update.message.reply_text(
            text=join_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # ইউজার ডাটা স্টোর
    if user_id not in user_data:
        user_data[user_id] = {
            'first_name': user.first_name,
            'join_date': datetime.now(TIMEZONE),
            'verified': True
        }
        active_users.add(user_id)
    
    # ওয়েলকাম মেসেজ পাঠান
    await send_welcome_message(user_id, context, user.first_name)

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """জয়েন ভেরিফিকেশন"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if await is_member(user_id, context):
        user_data[user_id] = {
            'first_name': query.from_user.first_name,
            'join_date': datetime.now(TIMEZONE),
            'verified': True
        }
        active_users.add(user_id)
        
        await send_welcome_message(user_id, context, query.from_user.first_name)
        await query.delete_message()
    else:
        await query.answer("❌ আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)

async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """ডেইলি রিমাইন্ডার"""
    for user_id in list(active_users):
        try:
            reminder_text = f"""
⏰ *আয়ের সময় এসেছে!* ⏰

{user_data[user_id]['first_name']}, আজকে আপনার আয় শুরু করুন!

💰 প্রতি ৫ মিনিটে নতুন আয়ের সুযোগ
"""
            keyboard = [
                [InlineKeyboardButton(
                    "⚡ এখনই শুরু করুন", 
                    web_app=WebAppInfo(url=MINI_APP_URL)
                )]
            ]
            
            await context.bot.send_message(
                chat_id=user_id,
                text=reminder_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Error sending reminder to {user_id}: {e}")

def main():
    # বট ইনিশিয়ালাইজ
    application = Application.builder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলার যোগ করুন
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify_join, pattern="^verify_join$"))
    
    # নোটিফিকেশন সেটআপ
    job_queue = application.job_queue
    job_queue.run_repeating(
        send_daily_reminder,
        interval=NOTIFICATION_INTERVAL,
        first=10
    )
    
    # বট শুরু করুন
    application.run_polling()

if __name__ == "__main__":
    main()

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
CHANNEL_USERNAME = "@EarningMasterbd24"  # @ সহ চ্যানেল ইউজারনেম
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

async def enforce_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """চ্যানেল মেম্বারশিপ ভেরিফিকেশন"""
    user = update.effective_user
    user_id = user.id
    
    if user_id == ADMIN_ID:
        return True
    
    if not await is_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("🔗 চ্যানেল জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔄 জয়েন ভেরিফাই করুন", callback_data="verify_join")]
        ]
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ *অ্যাক্সেস ডিনাইড*\n\n"
                 "এই বট ব্যবহার করতে আপনাকে অবশ্যই আমাদের চ্যানেলে জয়েন করতে হবে:\n"
                 f"{CHANNEL_USERNAME}\n\n"
                 "জয়েন করার পর ভেরিফাই বাটনে ক্লিক করুন",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if not await enforce_membership(update, context):
        return
    
    # ইউজার ডাটা স্টোর করুন
    if user_id not in user_data:
        user_data[user_id] = {
            'first_name': user.first_name,
            'join_date': datetime.now(TIMEZONE),
            'verified': True
        }
        active_users.add(user_id)
    
    if user_id == ADMIN_ID:
        # এডমিন ইন্টারফেস
        keyboard = [
            [InlineKeyboardButton("📊 ড্যাশবোর্ড", callback_data="admin_dashboard")],
            [InlineKeyboardButton("🚀 অ্যাপ ওপেন করুন", web_app=WebAppInfo(url=MINI_APP_URL))]
        ]
        await update.message.reply_text(
            text=f"👑 *এডমিন ড্যাশবোর্ড*\n\n"
                 f"স্বাগতম {user.first_name}!\n"
                 f"বর্তমান সক্রিয় ইউজার: {len(active_users)}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # নরমাল ইউজার ইন্টারফেস
        button = InlineKeyboardButton(
            "💰 আয় শুরু করুন", 
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
        await update.message.reply_text(
            text=f"🌟 *ইয়ার্নিং মাস্টারে স্বাগতম*\n\n"
                 f"হ্যালো {user.first_name}, আয় শুরু করতে নিচের বাটনে ক্লিক করুন:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[button]])
        )

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """জয়েন ভেরিফিকেশন হ্যান্ডলার"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if await is_member(user_id, context):
        user_data[user_id]['verified'] = True
        active_users.add(user_id)
        
        button = InlineKeyboardButton(
            "🚀 আয় শুরু করুন", 
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
        await query.edit_message_text(
            text="✅ *ভেরিফিকেশন সফল*\n\n"
                 "আপনি এখন ইয়ার্নিং মাস্টার ব্যবহার করতে পারবেন!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[button]])
        )
    else:
        await query.answer("আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)

async def send_notifications(context: ContextTypes.DEFAULT_TYPE):
    """নোটিফিকেশন সিস্টেম"""
    for user_id in list(active_users):
        try:
            if not user_data.get(user_id, {}).get('verified', False):
                continue
                
            button = InlineKeyboardButton(
                "⚡ আয় করুন", 
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="🕒 *আয়ের সেরা সময় এখনই!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[button]])
            )
        except Exception as e:
            logger.error(f"Error sending notification to {user_id}: {e}")

def main():
    # বট ইনিশিয়ালাইজেশন
    application = Application.builder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলার যোগ করুন
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify_join, pattern="^verify_join$"))
    application.add_handler(CallbackQueryHandler(start, pattern="^admin_dashboard$"))
    
    # নোটিফিকেশন জব সেটআপ
    job_queue = application.job_queue
    job_queue.run_repeating(
        send_notifications,
        interval=NOTIFICATION_INTERVAL,
        first=10
    )
    
    # বট শুরু করুন
    application.run_polling()

if __name__ == "__main__":
    main()

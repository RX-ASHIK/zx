# -*- coding: utf-8 -*-
"""
💰 EARNING MASTER BOT - Complete Bilingual Version
📱 Version: 11.0 | Codename: "Complete Earner"
"""

import asyncio
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configuration
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1"
SUPPORT_USERNAME = "@EarningMaster_help"
ADMIN_ID = 5989402185

# Database Setup
def init_db():
    conn = sqlite3.connect('earning_master.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        balance REAL DEFAULT 0,
        referral_count INTEGER DEFAULT 0,
        join_date TEXT DEFAULT CURRENT_TIMESTAMP,
        last_active TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        sent_time TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

init_db()

class EarningMasterBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("miniapp", self.open_mini_app))
        self.application.add_handler(CommandHandler("support", self.support))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self._register_user(user)
        
        keyboard = [
            [InlineKeyboardButton("📱 মিনি অ্যাপ খুলুন", callback_data="open_miniapp")],
            [InlineKeyboardButton("📊 ড্যাশবোর্ড", callback_data="dashboard")],
            [InlineKeyboardButton("🛎️ Customer Support", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")]
        ]
        
        await update.message.reply_text(
            "🌟 <b>Earning Master এ স্বাগতম!</b> 🌟\n\n"
            "আমাদের সাথে টাকা উপার্জন করুন:\n"
            "▫️ মিনি অ্যাপ ব্যবহার করে\n"
            "▫️ বিভিন্ন টাস্ক সম্পন্ন করে\n\n"
            "<i>Start your earning journey today!</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        # Send welcome notification
        await self._send_notification(user.id, "নতুন ইউজার রেজিস্ট্রেশন")

    async def open_mini_app(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📱 Open Mini App Now", web_app={"url": MINI_APP_URL})],
            [InlineKeyboardButton("🔙 ড্যাশবোর্ডে ফিরে যান", callback_data="dashboard")]
        ]
        
        await update.message.reply_text(
            "🚀 <b>মিনি অ্যাপ ইনকাম সিস্টেম</b> 🚀\n\n"
            "এখানে আপনি পাবেন:\n"
            "▫️ অতিরিক্ত ইনকামের সুযোগ\n"
            "▫️ স্পেশাল বোনাস\n\n"
            "<i>Click below to open the mini app</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        conn = sqlite3.connect('earning_master.db')
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user.id,))
        balance = cursor.fetchone()[0]
        conn.close()
        
        keyboard = [
            [InlineKeyboardButton("📱 মিনি অ্যাপ", callback_data="open_miniapp")],
            [InlineKeyboardButton("💼 Earnings Report", callback_data="earnings")],
            [InlineKeyboardButton("🛎️ সাপোর্ট", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")]
        ]
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📊 <b>আপনার ড্যাশবোর্ড</b> 📊\n\n"
                 f"💰 বর্তমান ব্যালেন্স: {balance:.2f} BDT\n"
                 f"👤 ইউজার: {user.first_name}\n\n"
                 "<i>Last updated: Just now</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    async def support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🛎️ <b>সাপোর্ট সিস্টেম</b> 🛎️\n\n"
            f"যেকোনো সমস্যায় যোগাযোগ করুন: {SUPPORT_USERNAME}\n"
            "আমরা ২৪/৭ আপনার সেবায় আছি।\n\n"
            "<i>Our support team is always ready to help you!</i>",
            parse_mode='HTML'
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "open_miniapp":
            await self._open_mini_app_callback(query)
        elif query.data == "dashboard":
            await self.show_dashboard(update, context)
        elif query.data == "earnings":
            await self._show_earnings(query)

    async def _open_mini_app_callback(self, query):
        keyboard = [
            [InlineKeyboardButton("📱 Open Mini App Now", web_app={"url": MINI_APP_URL})],
            [InlineKeyboardButton("🔙 Back", callback_data="dashboard")]
        ]
        
        await query.edit_message_text(
            text="🚀 <b>Mini App Earning Portal</b> 🚀\n\n"
                 "Click below to open our mini app and start earning:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    async def _show_earnings(self, query):
        keyboard = [
            [InlineKeyboardButton("📊 Dashboard", callback_data="dashboard")],
            [InlineKeyboardButton("📱 মিনি অ্যাপ", callback_data="open_miniapp")]
        ]
        
        await query.edit_message_text(
            text="💼 <b>Your Earnings Report</b> 💼\n\n"
                 "▫️ Today: 0.00 BDT\n"
                 "▫️ This Week: 0.00 BDT\n"
                 "▫️ Total: 0.00 BDT\n\n"
                 "<i>Earn more using our mini app!</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    def _register_user(self, user):
        conn = sqlite3.connect('earning_master.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name, user.last_name)
        )
        conn.commit()
        conn.close()

    async def _send_notification(self, user_id: int, message: str):
        try:
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(
                chat_id=user_id,
                text=f"🔔 <b>Notification</b> 🔔\n\n{message}"
            )
            
            conn = sqlite3.connect('earning_master.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
                (user_id, message)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")

    async def send_initial_notifications(self):
        """Send notifications to all users when bot starts"""
        conn = sqlite3.connect('earning_master.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()
        
        for user in users:
            await self._send_notification(
                user[0],
                "📢 বটটি আপডেট করা হয়েছে!\n\n"
                "নতুন ফিচার সহ এখন আরও ভালোভাবে উপার্জন করুন।\n\n"
                "<i>Start earning now with better rewards!</i>"
            )

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    bot = EarningMasterBot()
    
    # Send initial notifications
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.send_initial_notifications())
    
    bot.application.run_polling()

if __name__ == "__main__":
    main()

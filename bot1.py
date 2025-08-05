# -*- coding: utf-8 -*-
"""
💰 EARNING MASTER BOT - বাংলা/English Mixed Version
📱 Version: 10.0 | Codename: "Bilingual Earner"
"""

import asyncio
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configuration
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1"
SUPPORT_USERNAME = "@EarningMaster_help"

class EarningMasterBot:
    def __init__(self):
        self.db = sqlite3.connect('earning_master.db')
        self.create_tables()
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def create_tables(self):
        cursor = self.db.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            join_date TEXT
        )
        ''')
        self.db.commit()
    
    async def send_initial_notifications(self):
        """বট শুরু হলে সকল ইউজারকে নোটিফিকেশন পাঠানো"""
        cursor = self.db.cursor()
        cursor.execute("SELECT user_id, first_name FROM users")
        users = cursor.fetchall()
        
        bot = Bot(token=BOT_TOKEN)
        
        for user_id, first_name in users:
            try:
                keyboard = [
                    [InlineKeyboardButton("📱 মিনি অ্যাপ খুলুন", web_app={"url": MINI_APP_URL})],
                    [InlineKeyboardButton("📊 ড্যাশবোর্ড", callback_data="dashboard")],
                    [InlineKeyboardButton("🛎️ সাপোর্ট", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")]
                ]
                
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🌟 <b>নতুন আপডেট!</b> 🌟\n\n"
                         f"হ্যালো {first_name}!\n"
                         "আমাদের সিস্টেম আপগ্রেড করা হয়েছে\n\n"
                         "✅ নতুন সুযোগসমূহ:\n"
                         "▫️ বেশি ইনকাম\n"
                         "▫️ দ্রুত উত্তোলন\n"
                         "▫️ নতুন টাস্ক\n\n"
                         "<i>Start earning now with better rewards!</i>",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                
            except Exception as e:
                logging.error(f"Failed to send notification to {user_id}: {str(e)}")
    
    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        self.application.add_handler(CommandHandler("support", self.support))
    
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
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "open_miniapp":
            await self.open_mini_app(update, context)
        elif query.data == "dashboard":
            await self.show_dashboard(update, context)
    
    async def open_mini_app(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📱 Open Mini App Now", web_app={"url": MINI_APP_URL})],
            [InlineKeyboardButton("🔙 ড্যাশবোর্ডে ফিরে যান", callback_data="dashboard")]
        ]
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🚀 <b>মিনি অ্যাপ ইনকাম সিস্টেম</b> 🚀\n\n"
                 "এখানে আপনি পাবেন:\n"
                 "▫️ অতিরিক্ত ইনকামের সুযোগ\n"
                 "▫️ স্পেশাল বোনাস\n\n"
                 "<i>Click below to open the mini app</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📱 মিনি অ্যাপ", callback_data="open_miniapp")],
            [InlineKeyboardButton("🛎️ সাপোর্ট", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
            [InlineKeyboardButton("💼 Earnings Report", callback_data="earnings")]
        ]
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📊 <b>আপনার ড্যাশবোর্ড</b> 📊\n\n"
                 "💰 বর্তমান ব্যালেন্স: 0.00 BDT\n"
                 "📱 মিনি অ্যাপ ইনকাম: 0.00 BDT\n\n"
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
    
    def _register_user(self, user):
        """নতুন ইউজার রেজিস্টার করা"""
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, first_name, last_name, join_date) VALUES (?, ?, ?, ?)",
            (user.id, user.first_name, user.last_name, datetime.now().isoformat())
        )
        self.db.commit()

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    bot = EarningMasterBot()
    
    # Send notifications when bot starts
    asyncio.get_event_loop().run_until_complete(bot.send_initial_notifications())
    
    bot.application.run_polling()

if __name__ == "__main__":
    main()

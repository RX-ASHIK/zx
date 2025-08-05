# -*- coding: utf-8 -*-
"""
💰 EARNING MASTER BOT - Complete Earning Solution
📱 Version: 6.0 | Codename: "Ultimate Earner"
"""

import os
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# ---------------------------- ⚙️ CONFIGURATION ⚙️ ---------------------------- #
BOT_TOKEN = "7641873839:AAHt4JsRYUMQDHrrEHdOB-No3ZrtJQeDxXc"
CHANNEL_USERNAME = "@EarningMasterbd24"
SUPPORT_USERNAME = "@EarningMaster_help"
ADMIN_ID = 5989402185
TIMEZONE = pytz.timezone("Asia/Dhaka")
MINI_APP_URL = "https://earningmaster244.blogspot.com/?m=1"  # আপনার মিনি অ্যাপ লিংক
DAILY_RESET_TIME = time(10, 0)  # 10:00 AM
NOTIFICATION_INTERVAL = 60  # 60 minutes = 1 hour

# ---------------------------- 🎨 EMOJI SYSTEM 🎨 ---------------------------- #
class Emoji:
    WELCOME = "🌟"
    MONEY = "💰"
    SUCCESS = "✅"
    ERROR = "❌"
    REFERRAL = "👥"
    SUPPORT = "🛎️"
    NOTIFICATION = "🔔"
    RESET = "🔄"
    AD = "📺"
    SURVEY = "📝"
    GAME = "🎮"
    DASHBOARD = "📊"
    TIME = "⏰"
    MINI_APP = "📱"

# ---------------------------- 📦 DATABASE MANAGER 📦 ---------------------------- #
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('earning_master.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            balance REAL DEFAULT 0,
            referral_count INTEGER DEFAULT 0,
            referred_by INTEGER,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            has_joined_channel BOOLEAN DEFAULT FALSE,
            ads_watched_today INTEGER DEFAULT 0,
            last_reset_date TEXT,
            last_notification_time TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            status TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        ''')
        
        self.conn.commit()
    
    def get_active_users(self) -> List[Tuple[int, str]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, first_name FROM users WHERE has_joined_channel = TRUE")
        return cursor.fetchall()
    
    def get_user(self, user_id: int) -> Optional[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

# ---------------------------- 🔔 NOTIFICATION SYSTEM 🔔 ---------------------------- #
class NotificationManager:
    def __init__(self, db: Database):
        self.db = db
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    def start_scheduler(self):
        """Start all scheduled notification jobs"""
        # Daily reset at 10 AM
        self.scheduler.add_job(
            self.send_daily_reset_notifications,
            'cron',
            hour=DAILY_RESET_TIME.hour,
            minute=DAILY_RESET_TIME.minute
        )
        
        # Hourly notifications
        self.scheduler.add_job(
            self.send_hourly_reminders,
            'interval',
            minutes=NOTIFICATION_INTERVAL,
            next_run_time=datetime.now(TIMEZONE) + timedelta(minutes=1)
        )
        
        self.scheduler.start()
    
    async def send_hourly_reminders(self):
        """Send hourly earning reminders to all active users"""
        active_users = self.db.get_active_users()
        bot = Bot(token=BOT_TOKEN)
        
        for user_id, first_name in active_users:
            try:
                message = (
                    f"{Emoji.NOTIFICATION} <b>Hourly Reminder for {first_name}</b> {Emoji.NOTIFICATION}\n\n"
                    f"{Emoji.MONEY} <i>Don't miss your earning opportunities!</i> {Emoji.MONEY}\n\n"
                    "📌 <b>Available Tasks:</b>\n"
                    f"{Emoji.AD} Watch ads\n"
                    f"{Emoji.SURVEY} Complete surveys\n"
                    f"{Emoji.GAME} Play games\n"
                    f"{Emoji.MINI_APP} Use our Mini App\n\n"
                    f"{Emoji.TIME} <i>Next reminder in 1 hour</i>"
                )
                
                keyboard = [
                    [InlineKeyboardButton(f"{Emoji.MONEY} Earn Now", callback_data="earn_now")],
                    [InlineKeyboardButton(f"{Emoji.MINI_APP} Open Mini App", web_app={"url": MINI_APP_URL})]
                ]
                
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                
                # Log notification
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "UPDATE users SET last_notification_time = ? WHERE user_id = ?",
                    (datetime.now(TIMEZONE).isoformat(), user_id)
                )
                cursor.execute(
                    "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
                    (user_id, "Hourly reminder sent")
                )
                self.db.conn.commit()
                
            except Exception as e:
                logging.error(f"Failed to send notification to {user_id}: {str(e)}")

    async def send_daily_reset_notifications(self):
        """Send daily reset notifications"""
        active_users = self.db.get_active_users()
        bot = Bot(token=BOT_TOKEN)
        
        for user_id, first_name in active_users:
            try:
                message = (
                    f"{Emoji.RESET} <b>Daily Reset Complete!</b> {Emoji.RESET}\n\n"
                    f"Good morning {first_name}!\n"
                    "All your daily tasks have been refreshed.\n\n"
                    "🎯 <b>New Opportunities:</b>\n"
                    "▫️ 50 new ads available\n"
                    "▫️ Fresh surveys\n"
                    "▫️ New games\n"
                    "▫️ Mini App rewards\n\n"
                    f"{Emoji.MONEY} <i>Start earning now!</i>"
                )
                
                keyboard = [
                    [InlineKeyboardButton(f"{Emoji.MINI_APP} Open Mini App", web_app={"url": MINI_APP_URL})],
                    [InlineKeyboardButton(f"{Emoji.MONEY} Earn Now", callback_data="earn_now")]
                ]
                
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                
            except Exception as e:
                logging.error(f"Failed to send reset notification to {user_id}: {str(e)}")

# ---------------------------- 📱 MINI APP MANAGER 📱 ---------------------------- #
class MiniAppManager:
    @staticmethod
    async def send_mini_app_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send message with mini app button"""
        keyboard = [
            [InlineKeyboardButton(f"{Emoji.MINI_APP} Open Mini App", web_app={"url": MINI_APP_URL})],
            [InlineKeyboardButton(f"{Emoji.DASHBOARD} Dashboard", callback_data="dashboard")]
        ]
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"{Emoji.MINI_APP} <b>Earning Mini App</b> {Emoji.MINI_APP}\n\n"
                "Get extra earnings through our mini app:\n"
                "▫️ More earning tasks\n"
                "▫️ Instant withdrawals\n"
                "▫️ Special bonuses\n\n"
                "Click below to open:"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

# ---------------------------- 🤖 MAIN BOT CLASS 🤖 ---------------------------- #
class EarningMasterBot:
    def __init__(self):
        self.db = Database()
        self.notification_manager = NotificationManager(self.db)
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("miniapp", self.open_mini_app))
        self.application.add_handler(CommandHandler("earn", self.earn_command))
        self.application.add_handler(CommandHandler("refer", self.refer_command))
        self.application.add_handler(CommandHandler("dashboard", self.show_dashboard))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self._register_user(user)
        
        keyboard = [
            [InlineKeyboardButton(f"{Emoji.MINI_APP} Open Mini App", callback_data="open_miniapp")],
            [InlineKeyboardButton(f"{Emoji.MONEY} Earn Money", callback_data="earn")],
            [InlineKeyboardButton(f"{Emoji.REFERRAL} Refer Friends", callback_data="refer")]
        ]
        
        await update.message.reply_text(
            f"{Emoji.WELCOME} <b>Welcome to Earning Master!</b> {Emoji.WELCOME}\n\n"
            "Earn money through:\n"
            f"▫️ {Emoji.AD} Watching ads\n"
            f"▫️ {Emoji.SURVEY} Completing surveys\n"
            f"▫️ {Emoji.GAME} Playing games\n"
            f"▫️ {Emoji.MINI_APP} Using our Mini App\n\n"
            "Choose an option below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def open_mini_app(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /miniapp command"""
        await MiniAppManager.send_mini_app_button(update, context)
    
    async def earn_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /earn command"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        earning_options = [
            {"emoji": Emoji.AD, "title": "Watch Ads", "earn": "0.10-1.00 BDT", "left": f"{50 - user_data[9]} left today"},
            {"emoji": Emoji.SURVEY, "title": "Complete Surveys", "earn": "5-20 BDT", "left": "Unlimited"},
            {"emoji": Emoji.GAME, "title": "Play Games", "earn": "1-10 BDT", "left": "10 left today"},
            {"emoji": Emoji.MINI_APP, "title": "Use Mini App", "earn": "3-15 BDT", "left": "Special rewards"}
        ]
        
        keyboard = []
        for option in earning_options:
            keyboard.append([
                InlineKeyboardButton(
                    f"{option['emoji']} {option['title']} (+{option['earn']}) - {option['left']}", 
                    callback_data=f"earn_{option['title'].lower().replace(' ', '_')}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton(f"{Emoji.MINI_APP} Open Mini App", web_app={"url": MINI_APP_URL})])
        keyboard.append([InlineKeyboardButton(f"{Emoji.DASHBOARD} Back to Dashboard", callback_data="dashboard")])
        
        await update.message.reply_text(
            f"{Emoji.MONEY} <b>Earning Opportunities</b> {Emoji.MONEY}\n\n"
            "💰 <i>Choose how you want to earn money:</i>\n\n"
            f"{Emoji.TIME} <b>Daily reset at 10 AM (GMT+6)</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def refer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refer command"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        referral_link = f"https://t.me/{context.bot.username}?start=ref_{user.id}"
        
        keyboard = [
            [InlineKeyboardButton(f"{Emoji.REFERRAL} Share Link", url=f"https://t.me/share/url?url={referral_link}&text=Join%20Earning%20Master%20to%20earn%20money!")],
            [InlineKeyboardButton(f"{Emoji.MINI_APP} Mini App Rewards", web_app={"url": MINI_APP_URL})],
            [InlineKeyboardButton(f"{Emoji.DASHBOARD} Dashboard", callback_data="dashboard")]
        ]
        
        await update.message.reply_text(
            f"{Emoji.REFERRAL} <b>Referral Program</b> {Emoji.REFERRAL}\n\n"
            f"🔗 <b>Your referral link:</b>\n<code>{referral_link}</code>\n\n"
            f"👥 <b>Total referrals:</b> <code>{user_data[5]}</code>\n"
            f"💰 <b>Earn {Config.REFERRAL_BONUS} BDT</b> for each successful referral!\n\n"
            "<i>Share your link with friends and earn together!</i>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user dashboard"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        dashboard = (
            f"{Emoji.DASHBOARD} <b>YOUR DASHBOARD</b> {Emoji.DASHBOARD}\n\n"
            f"👤 <b>User:</b> {user.first_name}\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"📅 <b>Joined:</b> {user_data[7].split()[0]}\n\n"
            f"{Emoji.MONEY} <b>Balance:</b> <code>{user_data[4]:.2f} BDT</code>\n"
            f"{Emoji.REFERRAL} <b>Referrals:</b> <code>{user_data[5]}</code>\n"
            f"{Emoji.AD} <b>Ads Watched:</b> <code>{user_data[9]}/50</code>\n\n"
            f"{Emoji.TIME} <i>Next notification in ~1 hour</i>"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"{Emoji.MINI_APP} Open Mini App", web_app={"url": MINI_APP_URL})],
            [InlineKeyboardButton(f"{Emoji.MONEY} Earn More", callback_data="earn")],
            [InlineKeyboardButton(f"{Emoji.REFERRAL} Refer Friends", callback_data="refer")]
        ]
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=dashboard,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "open_miniapp":
            await MiniAppManager.send_mini_app_button(update, context)
        elif query.data == "earn":
            await self.earn_command(update, context)
        elif query.data == "refer":
            await self.refer_command(update, context)
        elif query.data == "dashboard":
            await self.show_dashboard(update, context)
        elif query.data.startswith("earn_"):
            await self._handle_earning_option(query)
    
    async def _handle_earning_option(self, query):
        """Handle earning option selection"""
        option = query.data[5:]  # Remove "earn_" prefix
        
        if option == "use_mini_app":
            await query.edit_message_text(
                f"{Emoji.MINI_APP} <b>Mini App Earning</b> {Emoji.MINI_APP}\n\n"
                "Click the button below to open our mini app and earn special rewards!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"{Emoji.MINI_APP} Open Now", web_app={"url": MINI_APP_URL})]
                ]),
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                f"{Emoji.MONEY} <b>Earning Started!</b> {Emoji.MONEY}\n\n"
                f"You selected: {option.replace('_', ' ').title()}\n\n"
                "Complete the task to earn money!",
                parse_mode='HTML'
            )
    
    def _register_user(self, user):
        """Register new user in database"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name, user.last_name)
        )
        self.db.conn.commit()

    def run(self):
        """Run the bot"""
        self.notification_manager.start_scheduler()
        self.application.run_polling()

# ---------------------------- 🚀 MAIN ENTRY POINT 🚀 ---------------------------- #
if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    bot = EarningMasterBot()
    bot.run()

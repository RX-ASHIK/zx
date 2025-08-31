"""
Telegram File-Gated Bot (Python, aiogram v3)
Legal + safe template for distributing digital files after:
  1) Channel-join verification, and
  2) Manual deposit verification (e.g., Bkash/Nagad 20৳)

⚠️ Use responsibly. Do NOT use this project to facilitate illegal network bypassing or TOS violations.

Setup steps
-----------
1) Python 3.10+
2) pip install -r requirements.txt  (create it with: aiogram==3.4.1, aiosqlite==0.20.0, python-dotenv==1.0.1)
3) Create .env with:
   BOT_TOKEN="8407557730:AAEqtnFtqQE1J9EJ5uhQlmnjjz_-1oftzVg"
   ADMIN_IDS="7338156650"   # comma-separated Telegram user IDs of admins
   CURRENCY="BDT"
   MIN_DEPOSIT="20"                 # minimum amount required
   PAYMENT_NUMBER="+881318135863"  # your Bkash/Nagad number
4) Run: python bot.py

Admin quickstart
----------------
- /add_channel @YourChannel   → add required channel for join verification
- /list_channels              → list channels to join
- /set_price 25               → set min deposit amount
- /upload <CATEGORY>          → reply to a file/document with this command to set/update deliverable for a category
- Categories are free text; you can use: OTT, YOUTUBE, SOCIAL, or any custom labels
- /files                      → show what files are configured
- /approve <user_id>          → approve a pending deposit for a user
- /reject <user_id>           → reject a pending deposit
- /broadcast <text>           → broadcast a message to all users

User flow
---------
/start → Menu
   • Verify Join  → checks all required channels
   • Deposit     → shows deposit instructions; user submits TX ID or screenshot
   • Get Files   → requires both join verified + deposit approved

DB schema (SQLite)
------------------
users(id INTEGER PRIMARY KEY, tg_id INTEGER UNIQUE, is_join_verified INTEGER, is_deposit_approved INTEGER,
      created_at TEXT, updated_at TEXT)
channels(id INTEGER PRIMARY KEY, username TEXT UNIQUE)
files(id INTEGER PRIMARY KEY, category TEXT, file_id TEXT, title TEXT, updated_at TEXT)
deposits(id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, method TEXT, tx_id TEXT, status TEXT, proof_file_id TEXT,
         created_at TEXT, updated_at TEXT)

"""
import asyncio
import os
import logging
from datetime import datetime
from typing import List

import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
CURRENCY = os.getenv("CURRENCY", "BDT")
MIN_DEPOSIT = float(os.getenv("MIN_DEPOSIT", "20"))
PAYMENT_NUMBER = os.getenv("PAYMENT_NUMBER", "")

if not BOT_TOKEN:
    raise SystemExit("Please set BOT_TOKEN in .env")

DB_PATH = "bot.db"


def now_ts() -> str:
    return datetime.utcnow().isoformat()


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER UNIQUE,
            is_join_verified INTEGER DEFAULT 0,
            is_deposit_approved INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            file_id TEXT,
            title TEXT,
            updated_at TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            method TEXT,
            tx_id TEXT,
            status TEXT,
            proof_file_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        await db.commit()


async def get_or_create_user(tg_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM users WHERE tg_id=?", (tg_id,))
        row = await cur.fetchone()
        if row:
            return row[0]
        await db.execute(
            "INSERT INTO users (tg_id, created_at, updated_at) VALUES (?,?,?)",
            (tg_id, now_ts(), now_ts()),
        )
        await db.commit()
        cur = await db.execute("SELECT id FROM users WHERE tg_id=?", (tg_id,))
        row = await cur.fetchone()
        return row[0]


async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Verify Join", callback_data="verify")
    kb.button(text="💳 Deposit", callback_data="deposit")
    kb.button(text="📦 Get Files", callback_data="files")
    kb.adjust(1)
    return kb.as_markup()


async def categories_kb() -> InlineKeyboardMarkup:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT DISTINCT category FROM files ORDER BY category")
        cats = [r[0] for r in await cur.fetchall()]
    kb = InlineKeyboardBuilder()
    for c in cats:
        kb.button(text=c, callback_data=f"cat:{c}")
    kb.adjust(1)
    return kb.as_markup()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await get_or_create_user(message.from_user.id)
    await message.answer(
        "<b>Welcome!</b>\n\nThis bot delivers digital files after you:\n"
        "1) Join required channels, and\n2) Make a small deposit for account verification.",
        reply_markup=main_menu_kb(),
    )


@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id):
        return
    text = (
        "<b>Admin Panel</b>\n"
        "/add_channel @username — add join-required channel\n"
        "/remove_channel @username — remove channel\n"
        "/list_channels — list channels\n"
        "/set_price <amount> — set minimum deposit\n"
        "/upload <CATEGORY> — reply to a file to set/update deliverable\n"
        "/files — list configured files\n"
        "/approve <user_id> — approve a user's pending deposit\n"
        "/reject <user_id> — reject a user's pending deposit\n"
        "/broadcast <text> — broadcast to all users"
    )
    await message.answer(text)


@dp.message(Command("add_channel"))
async def add_channel(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return
    if not command.args:
        await message.reply("Usage: /add_channel @username")
        return
    username = command.args.strip()
    if not username.startswith("@"):
        await message.reply("Provide a @username")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO channels (username) VALUES (?)", (username,))
            await db.commit()
            await message.reply(f"Added {username}")
        except Exception as e:
            await message.reply(f"Error: {e}")


@dp.message(Command("remove_channel"))
async def remove_channel(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return
    if not command.args:
        await message.reply("Usage: /remove_channel @username")
        return
    username = command.args.strip()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE username=?", (username,))
        await db.commit()
    await message.reply(f"Removed {username}")


@dp.message(Command("list_channels"))
async def list_channels(message: Message):
    if not await is_admin(message.from_user.id):
        return
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT username FROM channels ORDER BY id")
        rows = await cur.fetchall()
    if not rows:
        await message.reply("No required channels set.")
    else:
        await message.reply("Required channels:\n" + "\n".join(u[0] for u in rows))


@dp.message(Command("set_price"))
async def set_price(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return
    global MIN_DEPOSIT
    try:
        amt = float(command.args.strip()) if command.args else None
    except Exception:
        amt = None
    if not amt or amt <= 0:
        await message.reply("Usage: /set_price <positive number>")
        return
    MIN_DEPOSIT = amt
    await message.reply(f"Minimum deposit set to {MIN_DEPOSIT} {CURRENCY}")


@dp.message(Command("upload"))
async def upload_file(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return
    if not command.args:
        await message.reply("Reply to a file with: /upload <CATEGORY>")
        return
    category = command.args.strip().upper()
    if not message.reply_to_message or not (message.reply_to_message.document or message.reply_to_message.video or message.reply_to_message.photo):
        await message.reply("Please reply to the file/document to upload.")
        return
    file_id = None
    title = None
    if message.reply_to_message.document:
        file_id = message.reply_to_message.document.file_id
        title = message.reply_to_message.document.file_name
    elif message.reply_to_message.video:
        file_id = message.reply_to_message.video.file_id
        title = "video"
    elif message.reply_to_message.photo:
        file_id = message.reply_to_message.photo[-1].file_id
        title = "image"
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM files WHERE category=?", (category,))
        row = await cur.fetchone()
        if row:
            await db.execute("UPDATE files SET file_id=?, title=?, updated_at=? WHERE id=?",
                             (file_id, title, now_ts(), row[0]))
        else:
            await db.execute("INSERT INTO files (category, file_id, title, updated_at) VALUES (?,?,?,?)",
                             (category, file_id, title, now_ts()))
        await db.commit()
    await message.reply(f"File set for category <b>{category}</b>.")


@dp.message(Command("files"))
async def list_files(message: Message):
    if not await is_admin(message.from_user.id):
        return
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, category, title, updated_at FROM files ORDER BY category")
        rows = await cur.fetchall()
    if not rows:
        await message.reply("No files uploaded.")
    else:
        text = "Configured files:\n" + "\n".join([f"• {r[1]} — {r[2]} (updated {r[3]})" for r in rows])
        await message.reply(text)


async def fetch_required_channels() -> List[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT username FROM channels ORDER BY id")
        return [r[0] for r in await cur.fetchall()]


async def check_membership(user_id: int) -> bool:
    channels = await fetch_required_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True


@dp.callback_query(F.data == "verify")
async def on_verify(callback: CallbackQuery):
    tg_id = callback.from_user.id
    await get_or_create_user(tg_id)
    channels = await fetch_required_channels()
    if not channels:
        await callback.message.edit_text("No channels are required right now.", reply_markup=main_menu_kb())
        return
    text = "Please join the channels below, then press <b>Re-check</b>:\n\n" + "\n".join(channels)
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.button(text=f"Open {ch}", url=f"https://t.me/{ch[1:]}")
    kb.button(text="🔁 Re-check", callback_data="recheck")
    kb.button(text="⬅️ Back", callback_data="back")
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup())


@dp.callback_query(F.data == "recheck")
async def on_recheck(callback: CallbackQuery):
    tg_id = callback.from_user.id
    uid = await get_or_create_user(tg_id)
    ok = await check_membership(tg_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_join_verified=?, updated_at=? WHERE tg_id=?",
                         (1 if ok else 0, now_ts(), tg_id))
        await db.commit()
    if ok:
        await callback.message.edit_text("✅ Join verification passed!", reply_markup=main_menu_kb())
    else:
        await callback.message.edit_text("❌ Not all channels joined yet. Please join them and try again.", reply_markup=main_menu_kb())


class DepositStates(StatesGroup):
    waiting_method = State()
    waiting_tx = State()
    waiting_proof = State()


@dp.callback_query(F.data == "deposit")
async def on_deposit(callback: CallbackQuery, state: FSMContext):
    await get_or_create_user(callback.from_user.id)
    text = (
        f"Minimum deposit: <b>{MIN_DEPOSIT} {CURRENCY}</b>\n\n"
        "Send your deposit method (type Bkash or Nagad) or type <code>cancel</code> to stop."
    )
    await state.set_state(DepositStates.waiting_method)
    await callback.message.edit_text(text)


@dp.message(DepositStates.waiting_method)
async def deposit_method(message: Message, state: FSMContext):
    if message.text and message.text.lower().strip() == "cancel":
        await state.clear()
        await message.answer("Cancelled.", reply_markup=main_menu_kb())
        return
    method = message.text.strip()
    if method.lower() not in ("bkash", "nagad"):
        await message.answer("Please type either 'Bkash' or 'Nagad' (without quotes).")
        return
    await state.update_data(method=method.title())
    await state.set_state(DepositStates.waiting_tx)
    await message.answer(f"Send your Transaction ID or short note for {method.title()}. Then send a screenshot/photo as proof.")


@dp.message(DepositStates.waiting_tx)
async def deposit_tx(message: Message, state: FSMContext):
    await state.update_data(tx=message.text.strip() if message.text else "")
    await state.set_state(DepositStates.waiting_proof)
    await message.answer("Now send the payment screenshot/photo (as image).")


@dp.message(DepositStates.waiting_proof)
async def deposit_proof(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Please send a photo (screenshot) as proof.")
        return
    data = await state.get_data()
    method = data.get("method", "?")
    tx_id = data.get("tx", "")
    proof_file_id = message.photo[-1].file_id

    async with aiosqlite.connect(DB_PATH) as db:
        uid = await get_or_create_user(message.from_user.id)
        await db.execute(
            "INSERT INTO deposits (user_id, amount, method, tx_id, status, proof_file_id, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (uid, MIN_DEPOSIT, method, tx_id, "pending", proof_file_id, now_ts(), now_ts()),
        )
        await db.commit()

    # notify admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id,
                proof_file_id,
                caption=(
                    f"<b>New deposit pending</b>\n"
                    f"User: <code>{message.from_user.id}</code> (@{message.from_user.username})\n"
                    f"Method: {method}\nTX: {tx_id}\nAmount: {MIN_DEPOSIT} {CURRENCY}\n\n"
                    f"Approve: /approve {message.from_user.id}\nReject: /reject {message.from_user.id}"
                ),
            )
        except Exception:
            pass

    await state.clear()
    await message.answer("Thanks! Your deposit is now <b>pending review</b>. You'll be notified after approval.", reply_markup=main_menu_kb())


@dp.message(Command("approve"))
async def approve_deposit(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.reply("Usage: /approve <user_id>")
        return
    tg_id = int(command.args.strip())

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM users WHERE tg_id=?", (tg_id,))
        urow = await cur.fetchone()
        if not urow:
            await message.reply("No such user.")
            return
        user_pk = urow[0]
        await db.execute("""
            UPDATE deposits SET status='approved', updated_at=?
            WHERE id = (
                SELECT id FROM deposits WHERE user_id=? AND status='pending' ORDER BY created_at DESC LIMIT 1
            )
        """, (now_ts(), user_pk))
        await db.execute("UPDATE users SET is_deposit_approved=1, updated_at=? WHERE tg_id=?", (now_ts(), tg_id))
        await db.commit()
    try:
        await bot.send_message(tg_id, "✅ Your deposit has been approved. You now have access to files.")
    except Exception:
        pass
    await message.reply("Approved.")


@dp.message(Command("reject"))
async def reject_deposit(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.reply("Usage: /reject <user_id>")
        return
    tg_id = int(command.args.strip())
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM users WHERE tg_id=?", (tg_id,))
        urow = await cur.fetchone()
        if not urow:
            await message.reply("No such user.")
            return
        user_pk = urow[0]
        await db.execute("""
            UPDATE deposits SET status='rejected', updated_at=?
            WHERE id = (
                SELECT id FROM deposits WHERE user_id=? AND status='pending' ORDER BY created_at DESC LIMIT 1
            )
        """, (now_ts(), user_pk))
        await db.commit()
    try:
        await bot.send_message(tg_id, "❌ Your deposit was rejected. Please contact support if needed.")
    except Exception:
        pass
    await message.reply("Rejected.")


@dp.callback_query(F.data == "files")
async def on_files(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT is_join_verified, is_deposit_approved FROM users WHERE tg_id=?", (callback.from_user.id,))
        row = await cur.fetchone()
    if not row:
        await callback.message.answer("Please /start first.")
        return
    join_ok, dep_ok = row
    if not join_ok:
        await callback.message.edit_text("Please verify channel join first.", reply_markup=main_menu_kb())
        return
    if not dep_ok:
        # show payment instructions with PAYMENT_NUMBER if set
        pay_text = f"Please deposit {MIN_DEPOSIT} {CURRENCY} to the following number:\n\n"
        if PAYMENT_NUMBER:
            pay_text += f"<b>{PAYMENT_NUMBER}</b>\n\nSend TX ID and screenshot via the Deposit menu.\n\n"
        pay_text += "After depositing, go to the Deposit → submit TX ID and screenshot. Admin will review."
        await callback.message.edit_text(pay_text, reply_markup=main_menu_kb())
        return
    kb = await categories_kb()
    await callback.message.edit_text("Choose a category to get the latest file:", reply_markup=kb)


@dp.callback_query(F.data.startswith("cat:"))
async def on_category(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT file_id, title FROM files WHERE category=?", (category,))
        row = await cur.fetchone()
    if not row:
        await callback.message.answer("No file set for this category yet.")
        return
    file_id, title = row
    try:
        await bot.send_document(callback.from_user.id, file_id, caption=f"{category} — {title}")
    except Exception:
        await callback.message.answer("Failed to send file. Admin might need to re-upload.")


@dp.message(Command("broadcast"))
async def broadcast(message: Message, command: CommandObject):
    if not await is_admin(message.from_user.id):
        return
    if not command.args:
        await message.reply("Usage: /broadcast <text>")
        return
    text = command.args
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT tg_id FROM users")
        users = [r[0] for r in await cur.fetchall()]
    sent = 0
    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            pass
    await message.reply(f"Broadcast sent to {sent} users.")


@dp.callback_query(F.data == "back")
async def on_back(callback: CallbackQuery):
    await callback.message.edit_text("Main menu:", reply_markup=main_menu_kb())


async def check_required_channels():
    """Check if at least one channel is required before starting the bot"""
    channels = await fetch_required_channels()
    if not channels:
        logger.warning("⚠️  No channels configured! Bot will not function properly.")
        logger.warning("Use /add_channel @channel_username to add required channels")
        return False
    return True


async def on_startup():
    await init_db()
    # Check if required channels are configured
    if not await check_required_channels():
        logger.warning("Bot started without required channels. Please add channels using /add_channel")
    
    # Send startup message to all admins
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🤖 Bot is now online and running!")
        except Exception as e:
            logger.error(f"Failed to send startup message to admin {admin_id}: {e}")


async def main():
    await on_startup()
    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
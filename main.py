import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============ CONFIG ============
TOKEN = "8662384922:AAH6AEptvxIUud8diSOuxGxTDpeJng_Jy8o"
ADMIN_CHAT_ID = 5665625481
CHANNEL_LINK = "https://t.me/+0e8y23kNRicyZTdl"
QR_IMAGE = "qr.png"
DB_FILE = "users.db"
# ================================


# ============ DATABASE ============
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    approved INTEGER DEFAULT 0
)
""")
conn.commit()


def add_user(user_id: int):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()


def approve_user(user_id: int):
    cur.execute("UPDATE users SET approved = 1 WHERE user_id = ?", (user_id,))
    conn.commit()


def is_approved(user_id: int) -> bool:
    cur.execute("SELECT approved FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    return row is not None and row[0] == 1


# ============ HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    add_user(user_id)

    if is_approved(user_id):
        await update.message.reply_text(
            "✅ Payment verified!\n\n"
            "🔓 Private channel link:\n"
            f"{CHANNEL_LINK}"
        )
    else:
        await update.message.reply_text(
            "👋 Welcome!\n\n"
            "💰 Please pay using the QR code below.\n"
            "📸 After payment, send screenshot here.\n\n"
            "⚠️ After approval, type /start again."
        )
        await update.message.reply_photo(photo=open(QR_IMAGE, "rb"))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    add_user(user.id)

    await update.message.reply_text(
        "✅ Payment screenshot received.\n"
        "⏳ Please wait for admin verification."
    )

    # Forward screenshot to admin
    await context.bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=update.message.chat_id,
        message_id=update.message.message_id,
    )

    # Notify admin
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            "💳 New payment proof\n\n"
            f"👤 User ID: {user.id}\n"
            f"👤 Username: @{user.username or 'No username'}\n\n"
            f"Approve with:\n/approve {user.id}"
        )
    )


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve USER_ID")
        return

    user_id = int(context.args[0])
    approve_user(user_id)

    await update.message.reply_text(
        "✅ User approved successfully.\n\n"
        "📢 User must type /start to receive channel link."
    )


# ============ MAIN ============
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()

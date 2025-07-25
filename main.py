import os
import requests
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- Bot Token and Unsplash API Key Configuration (Read from Environment Variables) ---
TELEGRAM_BOT_TOKEN = os.getenv("8272435714:AAG5tLuSPB7Z8YBZ6GU4ANZNgx1q2sCN93M")
UNSPLASH_ACCESS_KEY = os.getenv("G6x-bBca_IegBCFwU529ErJNinBVdXNWjSt4FOx8Od0")

# --- Admin IDs List ---
# REPLACE WITH YOUR TELEGRAM USER ID!
# To find your Telegram user ID, you can forward a message from yourself to @userinfobot
ADMIN_IDS = [7688936522] # Example: Replace with your Telegram ID
                                  # If there's more than one admin, separate with commas

# Unsplash API URL
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

# --- Admin Check Function ---
def is_admin(user_id: int) -> bool:
    """Checks if the given user_id is an admin."""
    return user_id in ADMIN_IDS

# --- General Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is received."""
    await update.message.reply_text(
        "Halo! 👋 Saya bot pencari foto Unsplash. Kirimkan kata kunci foto yang ingin kamu cari, "
        "misalnya 'kucing lucu' atau 'pemandangan gunung'."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is received."""
    await update.message.reply_text(
        "Untuk mencari foto, cukup ketikkan kata kunci yang kamu inginkan. "
        "Contoh: 'bunga mawar', 'sunset di pantai'.\n"
        "Saya akan mencoba mencarikan 3 foto terbaik untukmu."
    )

async def search_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Searches for photos on Unsplash based on the user's keyword."""
    query = update.message.text
    if not query:
        await update.message.reply_text("Mohon masukkan kata kunci untuk mencari foto.")
        return

    params = {
        "query": query,
        "client_id": UNSPLASH_ACCESS_KEY,
        "per_page": 3
    }

    try:
        response = requests.get(UNSPLASH_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data and data["results"]:
            photos = data["results"]
            media = []
            for photo in photos:
                if "urls" in photo and "regular" in photo["urls"]:
                    media.append(InputMediaPhoto(media=photo["urls"]["regular"]))

            if media:
                await update.message.reply_media_group(media=media)
                await update.message.reply_text(f"Ini dia 3 foto terbaik untuk '{query}' dari Unsplash.")
            else:
                await update.message.reply_text(f"Maaf, tidak ada foto yang ditemukan untuk '{query}'. Coba kata kunci lain.")
        else:
            await update.message.reply_text(f"Maaf, tidak ada foto yang ditemukan untuk '{query}'. Coba kata kunci lain.")

    except requests.exceptions.RequestException as e:
        print(f"Error calling Unsplash API: {e}")
        await update.message.reply_text(
            "Maaf, terjadi kesalahan saat mencoba mengambil foto. Silakan coba lagi nanti."
        )
    except Exception as e:
        print(f"Unexpected error: {e}")
        await update.message.reply_text(
            "Terjadi kesalahan yang tidak terduga. Mohon laporkan jika ini sering terjadi."
        )

# --- Admin Commands (Admin-Specific Menu) ---
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the admin menu if the user is an admin."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Maaf, kamu tidak memiliki akses ke menu ini.")
        return

    keyboard = [
        [InlineKeyboardButton("Info Pengguna", callback_data="admin_info_pengguna")],
        [InlineKeyboardButton("Log Bot", callback_data="admin_log_bot")],
        [InlineKeyboardButton("Broadcast Pesan", callback_data="admin_broadcast")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selamat datang di menu Admin:", reply_markup=reply_markup)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callbacks from admin menu buttons."""
    query = update.callback_query
    await query.answer() # Important to remove loading state from the button

    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("Maaf, kamu tidak memiliki akses ke fungsi ini.")
        return

    data = query.data

    if data == "admin_info_pengguna":
        # Example: Get bot and user info
        bot_info = await context.bot.get_me()
        response_text = (
            f"**Bot Info:**\n"
            f"ID: `{bot_info.id}`\n"
            f"Name: `{bot_info.first_name}`\n"
            f"Username: `@{bot_info.username}`\n\n"
            f"**Admin Info (You):**\n"
            f"Your ID: `{user_id}`\n"
            f"Your Username: `@{query.from_user.username}`"
        )
        await query.edit_message_text(response_text, parse_mode='Markdown')
    elif data == "admin_log_bot":
        # In a hosting environment, you need a way to access logs.
        # This is just a placeholder. May require integration with a logging service.
        await query.edit_message_text("Log viewing function not fully implemented. Check your logs in the Pella.app dashboard.")
    elif data == "admin_broadcast":
        await query.edit_message_text("Broadcast feature not implemented. You can add its logic here.")

# --- Main Function ---
def main() -> None:
    """Runs the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    if not TELEGRAM_BOT_TOKEN or not UNSPLASH_ACCESS_KEY:
        print("Error: TELEGRAM_BOT_TOKEN or UNSPLASH_ACCESS_KEY not found in environment variables.")
        print("Make sure you have set them in Pella.app.")
        exit(1)

    # General Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Admin Command Handlers
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    # Text Message Handler for Photo Search
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_photos))

    # Run the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

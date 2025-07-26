import os
import logging
import requests
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPAI_API_KEY = os.getenv('DEEPAI_API_KEY')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Kirimkan saya foto yang ingin kamu tingkatkan resolusinya (HD)."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kirim foto, dan saya akan membuatnya menjadi HD dengan AI."
    )

async def upscale_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Mohon kirimkan foto saja ya!")
        return
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()

    response = requests.post(
        "https://api.deepai.org/api/torch-srgan",
        files={'image': BytesIO(file_bytes)},
        headers={'api-key': DEEPAI_API_KEY}
    )

    if response.status_code != 200:
        await update.message.reply_text(
            f"Gagal memproses foto.\nStatus code: {response.status_code}\nResponse: {response.text}"
        )
        return

    result_url = response.json().get('output_url')
    if not result_url:
        await update.message.reply_text("API tidak mengembalikan hasil yang valid.")
        return
    
    r = requests.get(result_url)
    if r.status_code != 200:
        await update.message.reply_text("Gagal mengunduh hasil foto.")
        return

    bio = BytesIO(r.content)
    bio.name = "upscale.jpg"
    bio.seek(0)

    await update.message.reply_photo(photo=InputFile(bio), caption="Foto sudah di-upscale ke HD!")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, upscale_photo))

    print("Bot berjalan...")
    await app.run_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

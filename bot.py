import os
import logging
import requests
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirim foto yang ingin kamu HD-kan.")

async def upscale_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Kirimkan foto, bukan file lain.")
        return

    await update.message.reply_text("Memproses foto... Mohon tunggu.")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    
    # Upload foto ke layanan file hosting sementara
    upload = requests.post("https://api.imgbb.com/1/upload", params={
        "key": "YOUR_IMGBB_API_KEY"
    }, files={
        "image": BytesIO(file_bytes)
    })

    if upload.status_code != 200:
        await update.message.reply_text("Gagal mengupload gambar.")
        return

    image_url = upload.json()['data']['url']

    # Panggil API Replicate
    replicate_response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "version": "92860eaa102f3e14f24a54a1d9d99ba3cbb25b2c24d6e72a3046c2e3c5e909d3",
            "input": {"img": image_url}
        }
    )

    if replicate_response.status_code != 201:
        await update.message.reply_text("Gagal mengirim ke API Replicate.")
        return

    prediction = replicate_response.json()
    prediction_url = prediction["urls"]["get"]

    # Tunggu hasil
    import time
    for _ in range(20):
        time.sleep(3)
        check = requests.get(prediction_url, headers={
            "Authorization": f"Token {REPLICATE_API_TOKEN}"
        })
        result = check.json()
        if result["status"] == "succeeded":
            output_url = result["output"]
            break
    else:
        await update.message.reply_text("Gagal memproses gambar.")
        return

    result_image = requests.get(output_url)
    bio = BytesIO(result_image.content)
    bio.name = "hd_photo.jpg"
    bio.seek(0)

    await update.message.reply_photo(photo=InputFile(bio), caption="Foto HD berhasil dibuat!")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, upscale_photo))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

import os
import logging
import requests
from io import BytesIO
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirimkan foto untuk saya HD-kan.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    byte_array = await file.download_as_bytearray()

    # Upload ke imgbb
    imgbb_url = "https://api.imgbb.com/1/upload"
    response = requests.post(
        imgbb_url,
        data={"key": IMGBB_API_KEY},
        files={"image": BytesIO(byte_array)}
    )
    if response.status_code != 200:
        await update.message.reply_text("Gagal upload ke imgbb.")
        return
    image_url = response.json()["data"]["url"]

    # Kirim ke replicate
    headers = {"Authorization": f"Token {REPLICATE_API_TOKEN}"}
    json_data = {
        "version": "92802090b800491b84ee126b00c38c1d5d9eff7ff69c65f059055d28d65c1f6b",
        "input": {"img": image_url}
    }

    rep = requests.post("https://api.replicate.com/v1/predictions", json=json_data, headers=headers)
    if rep.status_code != 201:
        await update.message.reply_text("Gagal memproses HD (Replicate error).")
        return

    prediction = rep.json()
    status = prediction["status"]
    get_url = prediction["urls"]["get"]

    # Tunggu hasilnya selesai diproses
    import time
    while status not in ["succeeded", "failed"]:
        time.sleep(2)
        poll = requests.get(get_url, headers=headers).json()
        status = poll["status"]

    if status == "succeeded":
        output_url = poll["output"]
        image_data = requests.get(output_url).content
        await update.message.reply_photo(photo=InputFile(BytesIO(image_data), filename="hd.jpg"), caption="Foto HD selesai!")
    else:
        await update.message.reply_text("Proses HD gagal.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot berjalan...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

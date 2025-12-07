import os
import logging
from fastapi import FastAPI
import uvicorn
from threading import Thread
from telegram.ext import Updater, MessageHandler, Filters
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FastAPI app to keep Render alive
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running on Render"}

# ------------------- DOWNLOAD FUNCTION ------------------- #

def download_720p(url):
    output_file = "video_720p.mp4"

    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": output_file,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_file


# ------------------- TELEGRAM MESSAGE HANDLER ------------------- #

def handle_message(update, context):
    url = update.message.text.strip()

    if "youtube" not in url and "youtu.be" not in url:
        update.message.reply_text("❌ Send a valid YouTube URL please.")
        return

    processing = update.message.reply_text("📥 Downloading 720p video...")

    try:
        file_path = download_720p(url)

        update.message.reply_video(
            video=open(file_path, "rb"),
            caption="✅ Here's your 720p video!"
        )

        os.remove(file_path)
        processing.edit_text("✔ Completed!")

    except Exception as e:
        logger.error(e)
        processing.edit_text("❌ Failed to download. Try another link.")


# ------------------- RUN TELEGRAM BOT ------------------- #

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()   # <-- OK IN THREAD
    # DO NOT CALL idle() !!!  # <-- THIS FIXES YOUR ERROR


# ------------------- MAIN ENTRY ------------------- #

if __name__ == "__main__":
    # Start Telegram bot in background
    Thread(target=run_bot, daemon=True).start()

    # Start FastAPI for Render
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

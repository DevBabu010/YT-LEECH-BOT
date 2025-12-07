import os
import logging
from fastapi import FastAPI
import uvicorn
from threading import Thread
from telegram.ext import Updater, MessageHandler, Filters
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------------- LOGGING ---------------- #

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- FASTAPI SERVER ---------------- #

app = FastAPI()

@app.get("/")
def home():
    return {"status": "YT Bot Running Successfully on Render!"}


# ---------------- VIDEO DOWNLOAD ---------------- #

def download_720p(url):
    output_path = "video_720p.mp4"

    ydl_opts = {
        "format": "bestvideo[height<=720]+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": output_path,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path


# ---------------- TELEGRAM HANDLER ---------------- #

def handle_message(update, context):
    url = update.message.text.strip()

    if "youtube" not in url and "youtu.be" not in url:
        update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    msg = update.message.reply_text("⬇️ Downloading 720p video...")

    try:
        path = download_720p(url)

        update.message.reply_video(video=open(path, "rb"), caption="🎉 Done!")

        os.remove(path)
        msg.edit_text("✔️ Completed!")

    except Exception as e:
        logger.error(str(e))
        msg.edit_text("❌ Error downloading video. Try another link.")


# ---------------- TELEGRAM BOT RUNNER ---------------- #

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


# ---------------- MAIN ENTRY POINT ---------------- #

if __name__ == "__main__":
    # Run Telegram bot in background thread (safe now)
    Thread(target=run_bot, daemon=True).start()

    # Start FastAPI server for Render
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

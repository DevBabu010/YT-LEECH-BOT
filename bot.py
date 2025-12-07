import os
import asyncio
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from yt_dlp import YoutubeDL

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running"}

COOKIES_FILE = "cookies.txt"


# ---------------------------
# DOWNLOAD FUNCTION
# ---------------------------
async def download_video(url: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Downloading… please wait ⏳")

    def run_yt():
        ydl_opts = {
            "format": "bestvideo[height<=720]+bestaudio/best",
            "outtmpl": "video.mp4",
            "merge_output_format": "mp4",
            "ffmpeg_location": "/usr/bin/ffmpeg",
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": 5,
        }

        # Use cookies.txt if exists
        if os.path.exists(COOKIES_FILE):
            ydl_opts["cookies"] = COOKIES_FILE
            logging.info("Using cookies.txt for YouTube login.")
        else:
            logging.warning("cookies.txt not found — downloading public videos only.")

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    # Run yt-dlp in background thread
    try:
        await asyncio.wait_for(asyncio.to_thread(run_yt), timeout=180)
    except asyncio.TimeoutError:
        return await update.message.reply_text("❌ Download timeout. Try again.")
    except Exception as e:
        return await update.message.reply_text(f"❌ Error: {e}")

    # Send video
    try:
        await update.message.reply_video(
            video=open("video.mp4", "rb"),
            caption="Here is your video 👍"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Telegram error: {e}")

    # Clean up
    try:
        os.remove("video.mp4")
    except:
        pass


# ---------------------------
# COMMAND HANDLERS
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me any YouTube link and I'll download the 720p video for you!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "youtube.com" in text or "youtu.be" in text:
        await download_video(text, update, context)
    else:
        await update.message.reply_text("❌ Please send a valid YouTube link.")


# ---------------------------
# RUN BOT
# ---------------------------
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

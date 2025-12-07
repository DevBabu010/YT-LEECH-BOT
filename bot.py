import os
import asyncio
import base64
import logging
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------------------
# FASTAPI HEARTBEAT SERVER
# ---------------------------
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot running"}


# ---------------------------
# COOKIE HANDLING
# ---------------------------
cookies_path = "cookies.txt"

if os.getenv("COOKIES_BASE64"):
    with open(cookies_path, "wb") as f:
        f.write(base64.b64decode(os.getenv("COOKIES_BASE64")))
    logging.info("Cookies loaded from environment.")
else:
    logging.info("No cookies provided. Public videos only.")


# ---------------------------
# DOWNLOAD FUNCTION
# ---------------------------
async def download_video(url: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⬇ Download started...\nPlease wait 10–20 seconds.")

    def run_yt():
        ydl_opts = {
            "format": "bestvideo[height<=720]+bestaudio/best",
            "outtmpl": "video.mp4",
            "merge_output_format": "mp4",
            "cookies": cookies_path if os.path.exists(cookies_path) else None,
            "ffmpeg_location": "/usr/bin/ffmpeg",
            "retries": 10,
            "fragment_retries": 10,
            "concurrent_fragment_downloads": 5,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    # Run download in background thread to prevent timeout
    try:
        await asyncio.wait_for(asyncio.to_thread(run_yt), timeout=120)
    except asyncio.TimeoutError:
        await update.message.reply_text("❌ Timeout occurred. Try again.")
        return
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return

    # Send file
    try:
        await update.message.reply_video(
            video=open("video.mp4", "rb"),
            caption="Here is your 720p video 😊"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Telegram send error: {e}")

    # Cleanup
    if os.path.exists("video.mp4"):
        os.remove("video.mp4")


# ---------------------------
# Telegram Bot Handlers
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a YouTube link and I'll download it in 720p!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" in url or "youtu.be" in url:
        await download_video(url, update, context)
    else:
        await update.message.reply_text("❌ Not a valid YouTube link.")


# ---------------------------
# MAIN APPLICATION
# ---------------------------
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

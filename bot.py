import os
import logging
import asyncio
import yt_dlp
import aiohttp

from telegram.ext import (
    Application,
    MessageHandler,
    filters,
)
from telegram import Update

# ---------------------------------------
# Logging
# ---------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------------------------------------
# Long Timeout Session (fixes upload errors)
# ---------------------------------------
session = aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(
        total=600,
        connect=600,
        sock_connect=600,
        sock_read=600
    )
)

# ---------------------------------------
# Download 720p with FFmpeg & Cookies
# ---------------------------------------
def download_720p(url):
    output_file = "video_720p.mp4"

    ydl_opts = {
        "cookiefile": "cookies.txt",   # You solved cookies already
        "format": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best",
        "merge_output_format": "mp4",

        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4"
            }
        ],

        "outtmpl": output_file,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_file

# ---------------------------------------
# Handle incoming messages
# ---------------------------------------
async def handle_message(update: Update, context):

    text = update.message.text.strip()

    if "youtu" not in text:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    status_msg = await update.message.reply_text("⬇️ Downloading video in 720p...")

    try:
        filepath = download_720p(text)

        await status_msg.edit_text("📤 Uploading video to Telegram (may take time)...")

        # LARGE TIMEOUT FIX
        with open(filepath, "rb") as f:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=f,
                supports_streaming=True,
                read_timeout=600,
                write_timeout=600,
                connect_timeout=600,
                timeout=600
            )

        await status_msg.edit_text("✅ Done!")

        os.remove(filepath)

    except Exception as e:
        logger.error(f"Download/Upload failed: {e}")
        await status_msg.edit_text("❌ Failed. Try another link.")

# ---------------------------------------
# Main Entry
# ---------------------------------------
async def main():
    app = Application.builder().token(BOT_TOKEN).client_session(session).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()
    await app.start()
    logger.info("Bot started successfully.")
    await asyncio.Event().wait()   # prevent exit


if __name__ == "__main__":
    asyncio.run(main())

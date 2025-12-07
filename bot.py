import os
import logging
from telegram.ext import Updater, MessageHandler, Filters
from telegram import ParseMode
import yt_dlp

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# -------------------- DOWNLOAD FUNCTION -------------------- #

def download_720p(url):
    output_path = "video_720p.mp4"

    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "outtmpl": output_path,
        "merge_output_format": "mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path


# -------------------- TELEGRAM HANDLER -------------------- #

def handle_message(update, context):
    url = update.message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    msg = update.message.reply_text("⬇️ Downloading video in 720p, please wait...")

    try:
        filepath = download_720p(url)

        update.message.reply_video(
            video=open(filepath, "rb"),
            caption="✅ Here is your 720p video!"
        )

        os.remove(filepath)
        msg.edit_text("✔️ Done!")

    except Exception as e:
        logger.error(e)
        msg.edit_text("❌ Failed to download video. Try another link.")


# -------------------- BOT RUNNER -------------------- #

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()  # now safe because running in main thread


if __name__ == "__main__":
    main()

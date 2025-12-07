#!/usr/bin/env python3
import os
import logging
import math
import tempfile
import threading
import requests

from fastapi import FastAPI
import uvicorn

from pytube import YouTube
from telegram import ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# ----------------------------------------------------
# ENVIRONMENT VARIABLES
# ----------------------------------------------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")

TELEGRAM_MAX_BYTES = int(os.getenv("TELEGRAM_MAX_BYTES", str(1900 * 1024 * 1024)))
CHAT_WHITELIST = os.getenv("CHAT_WHITELIST")

# ----------------------------------------------------
# FASTAPI SERVER (so Render Free Web Service won't stop)
# ----------------------------------------------------
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Telegram YouTube Downloader Bot running on Render!"}

# ----------------------------------------------------
# LOGGING
# ----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------
# PROGRESS TRACKER
# ----------------------------------------------------
class ProgressState:
    def __init__(self):
        self.chat_message = None
        self.last_percent = -1

progress = ProgressState()

def on_progress(stream, chunk, bytes_remaining):
    try:
        total_size = stream.filesize
        downloaded = total_size - bytes_remaining
        percent = math.floor(downloaded / total_size * 100)
    except:
        return

    if progress.chat_message and percent != progress.last_percent:
        try:
            progress.chat_message.edit_text(f"Downloading… {percent}%")
            progress.last_percent = percent
        except:
            pass

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------
def normalize_youtube_url(url):
    """Convert embed links to normal YouTube watch links."""
    if "youtube.com/embed/" in url:
        video_id = url.split("embed/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def human_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h: return f"{h}h {m}m {s}s"
    if m: return f"{m}m {s}s"
    return f"{s}s"

def choose_stream(yt):
    """Pick the best progressive MP4 stream."""
    stream = yt.streams.filter(progressive=True, file_extension="mp4", res="720p").first()
    if stream: return stream

    stream = yt.streams.filter(progressive=True, file_extension="mp4", res="480p").first()
    if stream: return stream

    return yt.streams.filter(progressive=True, file_extension="mp4")\
                     .order_by("resolution")\
                     .desc()\
                     .first()

# ----------------------------------------------------
# BOT COMMANDS
# ----------------------------------------------------
def start(update, context):
    update.message.reply_text(
        "👋 Send me any YouTube link and I will download the video in 720p (or best available)."
    )

def handle_message(update, context):
    chat_id = str(update.effective_chat.id)

    if CHAT_WHITELIST:
        allowed = CHAT_WHITELIST.split(",")
        if chat_id not in allowed:
            return update.message.reply_text("You are not allowed to use this bot.")

    url = update.message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        return update.message.reply_text("❌ Please send a valid YouTube URL.")

    url = normalize_youtube_url(url)

    status_msg = update.message.reply_text("Starting download…")
    progress.chat_message = status_msg
    progress.last_percent = -1

    update.message.chat.send_action(ChatAction.UPLOAD_VIDEO)

    try:
        yt = YouTube(url, on_progress_callback=on_progress)
    except Exception:
        status_msg.edit_text("❌ Error: Unable to access YouTube video.")
        return

    stream = choose_stream(yt)
    if not stream:
        return status_msg.edit_text("❌ No downloadable MP4 stream found.")

    if stream.filesize > TELEGRAM_MAX_BYTES:
        return status_msg.edit_text("❌ Video is too large for Telegram upload (>2GB).")

    tmp_dir = tempfile.mkdtemp(dir="/tmp")
    filepath = os.path.join(tmp_dir, "video.mp4")

    try:
        status_msg.edit_text("Downloading… 0%")
        stream.download(output_path=tmp_dir, filename="video.mp4")
    except Exception:
        status_msg.edit_text("❌ Download failed.")
        return

    # download thumbnail
    thumb_path = None
    try:
        r = requests.get(yt.thumbnail_url)
        thumb_path = os.path.join(tmp_dir, "thumb.jpg")
        with open(thumb_path, "wb") as f:
            f.write(r.content)
    except:
        thumb_path = None

    caption = (
        f"📽 <b>{yt.title}</b>\n"
        f"⏳ Duration: {human_duration(yt.length)}\n"
        f"🎞 Quality: {stream.resolution}"
    )

    try:
        with open(filepath, "rb") as vid:
            if thumb_path:
                with open(thumb_path, "rb") as th:
                    update.message.reply_video(
                        video=vid,
                        thumb=th,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
            else:
                update.message.reply_video(
                    video=vid,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
        status_msg.edit_text("✅ Upload complete!")
    except Exception:
        status_msg.edit_text("❌ Upload failed.")

    progress.chat_message = None

    try:
        os.remove(filepath)
        if thumb_path:
            os.remove(thumb_path)
        os.rmdir(tmp_dir)
    except:
        pass

# ----------------------------------------------------
# BOT RUNNER
# ----------------------------------------------------
def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

# ----------------------------------------------------
# START BOTH FASTAPI + BOT
# ----------------------------------------------------
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

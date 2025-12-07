#!/usr/bin/env python3
"""
Telegram YouTube Downloader Bot
Features:
 - Accepts normal and embed YouTube links
 - Attempts to download 720p progressive MP4, fallback to 480p or best progressive mp4
 - Progress updates (edit message)
 - Sends thumbnail, title, duration, and file as video
 - Stores files in /tmp and cleans up
 - Rejects videos larger than TELEGRAM_MAX_BYTES (default ~1.9GB)
"""
import os
import logging
import tempfile
import math
import requests
from pytube import YouTube
from telegram import ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# --- Configuration from environment variables ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")

# Maximum allowed file size to attempt upload (bytes). Default ~1.9GB to be safe under Telegram 2GB.
TELEGRAM_MAX_BYTES = int(os.getenv("TELEGRAM_MAX_BYTES", str(1900 * 1024 * 1024)))

# Optional: limit to only a single chat or admin (set CHAT_WHITELIST to comma-separated chat ids)
CHAT_WHITELIST = os.getenv("CHAT_WHITELIST")  # e.g. "123456789,987654321"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Progress callback state holder
class ProgressState:
    def __init__(self):
        self.chat_message = None
        self.last_percent = -1

progress_state = ProgressState()


def start(update, context):
    update.message.reply_text(
        "Send me a YouTube link (or embed link). I will try to download it in 720p (fallbacks to best available)."
    )


def normalize_youtube_url(url: str) -> str:
    """Convert embed link to normal watch url."""
    if "youtube.com/embed/" in url:
        video_id = url.split("embed/")[1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def on_progress(stream, chunk, bytes_remaining):
    """pytube progress callback; edits the status message with percent."""
    try:
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percent = math.floor(bytes_downloaded / total_size * 100)
    except Exception:
        return

    # reduce frequent edits
    if progress_state.last_percent != percent and progress_state.chat_message:
        try:
            progress_state.chat_message.edit_text(f"Downloading… {percent}%")
            progress_state.last_percent = percent
        except Exception:
            pass


def choose_stream(yt: YouTube):
    """Choose best progressive mp4 - prioritize 720p, then 480p, then best progressive."""
    # progressive=True means audio+video combined
    stream = yt.streams.filter(progressive=True, file_extension="mp4", res="720p").first()
    if stream:
        return stream
    stream = yt.streams.filter(progressive=True, file_extension="mp4", res="480p").first()
    if stream:
        return stream
    # fallback: highest resolution progressive mp4 available
    return yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()


def human_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def handle_message(update, context):
    # whitelist check (optional)
    if CHAT_WHITELIST:
        allowed = [c.strip() for c in CHAT_WHITELIST.split(",") if c.strip()]
        if str(update.effective_chat.id) not in allowed:
            update.message.reply_text("This bot is restricted.")
            return

    url = update.message.text.strip()
    if not url:
        update.message.reply_text("Please send a YouTube link.")
        return

    if "youtube.com" not in url and "youtu.be" not in url:
        update.message.reply_text("Please send a valid YouTube URL (including embed links).")
        return

    url = normalize_youtube_url(url)
    # Send initial status message and set progress
    status_msg = update.message.reply_text("Starting download…")
    progress_state.chat_message = status_msg
    progress_state.last_percent = -1

    # Set ChatAction for upload
    update.message.chat.send_action(action=ChatAction.UPLOAD_VIDEO)

    try:
        # Initialize YouTube with progress callback
        yt = YouTube(url, on_progress_callback=on_progress)
    except Exception as e:
        logger.exception("Error creating YouTube object")
        status_msg.edit_text("Failed to access YouTube video. Possibly invalid or blocked.")
        progress_state.chat_message = None
        return

    # Choose stream
    stream = choose_stream(yt)
    if not stream:
        status_msg.edit_text("No suitable progressive mp4 stream found for this video.")
        progress_state.chat_message = None
        return

    # Size check before downloading (if pytube provides it)
    try:
        filesize = stream.filesize  # bytes
    except Exception:
        filesize = None

    if filesize and filesize > TELEGRAM_MAX_BYTES:
        status_msg.edit_text(
            "The selected video is too large to upload to Telegram (>{} bytes).".format(TELEGRAM_MAX_BYTES)
        )
        progress_state.chat_message = None
        return

    # Download into temp file
    tmp_dir = tempfile.mkdtemp(dir="/tmp")
    filename = os.path.join(tmp_dir, "video.mp4")

    try:
        status_msg.edit_text("Downloading… 0%")
        # stream.download accepts output_path and filename
        stream.download(output_path=tmp_dir, filename="video.mp4")
    except Exception as e:
        logger.exception("Download failed")
        status_msg.edit_text("Download failed. The video might be blocked or pytube couldn't fetch it.")
        # cleanup
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception:
            pass
        progress_state.chat_message = None
        return

    # Final sanity filesize check
    try:
        actual_size = os.path.getsize(filename)
        if actual_size > TELEGRAM_MAX_BYTES:
            status_msg.edit_text("Downloaded file is too large to upload to Telegram.")
            os.remove(filename)
            progress_state.chat_message = None
            return
    except Exception:
        pass

    # Download thumbnail
    thumb_path = None
    try:
        thumbnail_url = yt.thumbnail_url
        if thumbnail_url:
            thumb_resp = requests.get(thumbnail_url, timeout=15)
            if thumb_resp.status_code == 200:
                thumb_path = os.path.join(tmp_dir, "thumb.jpg")
                with open(thumb_path, "wb") as f:
                    f.write(thumb_resp.content)
    except Exception:
        thumb_path = None

    # Prepare caption
    title = yt.title or "YouTube Video"
    duration = human_duration(int(yt.length or 0))
    caption = f"📽 <b>{title}</b>\n⏳ Duration: {duration}\nQuality: {stream.resolution or 'auto'}"
    try:
        # Send video
        with open(filename, "rb") as video_f:
            if thumb_path and os.path.exists(thumb_path):
                with open(thumb_path, "rb") as thumb_f:
                    update.message.reply_video(
                        video=video_f,
                        thumb=thumb_f,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                    )
            else:
                update.message.reply_video(
                    video=video_f,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )
        status_msg.edit_text("Upload complete ✅")
    except Exception:
        logger.exception("Upload failed")
        status_msg.edit_text("Video upload failed. Possibly too large for Telegram or network error.")
    finally:
        # Cleanup files and reset progress state
        try:
            if os.path.exists(filename):
                os.remove(filename)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            if os.path.exists(tmp_dir):
                os.rmdir(tmp_dir)
        except Exception:
            pass
        progress_state.chat_message = None


def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start Polling
    logger.info("Starting bot polling...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

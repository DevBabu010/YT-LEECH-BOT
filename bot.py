import threading
import os
import logging
from fastapi import FastAPI
import uvicorn

from pytube import YouTube
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction, ParseMode

# --- BOT TOKEN ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is missing")

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running on Render free web service!"}

# ---- YOUR BOT CODE (same as before) ----
# keep your previous bot code here (handle_message, start, download logic, etc.)

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

# Start the bot in background thread
threading.Thread(target=run_bot, daemon=True).start()

# Start web server for Render
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

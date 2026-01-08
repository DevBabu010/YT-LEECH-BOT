# YT-LEECH-BOT 🤖📥

A lightweight and efficient **Telegram bot** that downloads media from Youtube and delivers it directly to users via Telegram.  
Designed with scalability in mind, container-ready, and deployable on cloud platforms like **Render** or **Docker-based services**.

---

## ✨ Features

- 📥 Download videos or audio from youtube via Telegram commands
- 🚀 Fast and reliable media processing
- 📦 Docker support for easy deployment
- ☁️ Cloud-ready (Render compatible)
- 🔐 Optional chat-level access restriction.
- 📏 Configurable maximum upload size

---

## 🛠 Tech Stack

- **Python**
- **python-telegram-bot**
- **yt-dlp**
- **Docker**
- **Render (deployment)**

---

## 📁 Project Structure

```text
.
├── bot.py              # Main bot logic
├── Dockerfile          # Docker configuration
├── render.yaml         # Render deployment config
├── requirements.txt    # Python dependencies
├── cookies.txt         # Cookies file (optional)
├── .dockerignore       # Docker ignore rules
├── LICENSE             # MIT License
└── README.md           # Project documentation

```
---

## ⚙️ Environment Variables

| Variable             | Description                                                           |
| -------------------- | --------------------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | **(Required)** Telegram Bot Token from BotFather                      |
| `TELEGRAM_MAX_BYTES` | *(Optional)* Max file size (in bytes) to upload (default ≈ 1.9GB)     |
| `CHAT_WHITELIST`     | *(Optional)* Comma-separated Telegram chat IDs allowed to use the bot |

## Getting Started

Clone the repository:
git clone https://github.com/DevBabu010/YT-LEECH-BOT.git
cd YT-LEECH-BOT

Install dependencies:
pip install -r requirements.txt

Set environment variable:
export TELEGRAM_BOT_TOKEN=your_bot_token_here

Run the bot:
python bot.py

## Deploy on Render

This repository includes a render.yaml file for one-click deployment on Render.

Steps:
1. Push the repository to GitHub
2. Open https://render.com
3. Create a new Web Service
4. Connect your GitHub repository.
5. Add required environment variables (TELEGRAM_BOT_TOKEN, optional others)
6. Click Deploy

## 🔐 Security Notes
Never commit your bot token
Use CHAT_WHITELIST to restrict access
Keep cookies.txt private

## 📄 License
MIT License – free to use, modify, and distribute.

## ⭐ Author
Shailendra kumar verma (DevBabu010)

If this project helped you, consider giving it a ⭐


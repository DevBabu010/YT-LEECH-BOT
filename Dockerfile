FROM python:3.11-slim

# ------------------------------
# Install FFmpeg (required for yt-dlp)
# ------------------------------
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ------------------------------
# Set working directory
# ------------------------------
WORKDIR /app

# ------------------------------
# Install Python dependencies
# ------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------
# Copy all project files
# ------------------------------
COPY . .

# ------------------------------
# Start Telegram Bot
# ------------------------------
CMD ["python", "bot.py"]

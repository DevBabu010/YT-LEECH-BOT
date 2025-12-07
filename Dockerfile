# Use official slim Python image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable stdout/stderr buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Create app user
RUN addgroup --system app && adduser --system --ingroup app app

# Install OS packages required by pytube/requests (ca-certificates)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2 \
    libxslt1.1 \
    libssl-dev \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy bot code
COPY bot.py /app/bot.py
COPY README.md /app/README.md

# Set user to non-root
USER app

# Use /tmp for downloads inside container (already system temp)
ENV TMPDIR=/tmp

# Command to run bot
CMD ["python", "bot.py"]

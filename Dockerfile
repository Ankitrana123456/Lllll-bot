# Use maintained Debian base
FROM python:3.11-slim-bookworm

# Install build tools & system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential ffmpeg curl git && \
    rm -rf /var/lib/apt/lists/*

# Copy project
WORKDIR /app
COPY . .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Start the bot
CMD ["python", "main.py"]

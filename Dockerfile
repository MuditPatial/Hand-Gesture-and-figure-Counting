FROM python:3.10-slim

# System deps needed by OpenCV headless + MediaPipe
# Note: libgl1-mesa-glx was renamed to libgl1 in Debian Bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (including the model)
COPY . .

# Render assigns a dynamic port via $PORT env var
ENV PORT=10000
EXPOSE 10000

CMD gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
    --workers 1 \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    "app:app"

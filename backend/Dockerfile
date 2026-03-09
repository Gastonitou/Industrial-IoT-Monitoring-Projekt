FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY config/ ./config/
COPY backend/ ./backend/

# Create log directory
RUN mkdir -p logs

CMD ["python", "-m", "backend.mqtt_subscriber"]

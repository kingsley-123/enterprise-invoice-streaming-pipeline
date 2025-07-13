FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY kafka_bridge.py .

# Run the bridge
CMD ["python", "kafka_bridge.py"]
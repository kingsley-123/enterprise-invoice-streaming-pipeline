import requests
import json
import time
from kafka import KafkaProducer

# Configuration
API_URL = "http://invoice-api:8000/invoices"
KAFKA_SERVERS = ["broker:29092"]
KAFKA_TOPIC = "invoice-stream"
POLL_INTERVAL = 5

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Track last processed invoice
last_processed = 0

print("Starting Kafka bridge")
print(f"API: {API_URL}")
print(f"Kafka: {KAFKA_TOPIC}")

try:
    while True:
        # Get new invoices from API
        response = requests.get(f"{API_URL}?offset={last_processed}&limit=50")
        invoices = response.json().get('data', [])
        
        # Send each invoice to Kafka
        for invoice in invoices:
            producer.send(KAFKA_TOPIC, value=invoice)
            print(f"Sent: {invoice.get('invoice_id', '')[:8]}")
            last_processed += 1
        
        # Wait before next poll
        time.sleep(POLL_INTERVAL)
        
except KeyboardInterrupt:
    print("Stopping bridge")
    producer.close()

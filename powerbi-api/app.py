# PowerBI API Bridge for MongoDB

from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Simple MongoDB connection
client = MongoClient("mongodb://powerbi:powerbi123@mongodb:27017/invoices?authSource=invoices")
db = client.invoices

@app.route('/invoices')
def invoices():
    """Get complete flattened invoices for PowerBI"""
    data = []
    for doc in db.streaming_invoices.find({}, {'_id': 0}).limit(1000):
        data.append({
            # Main invoice fields
            'invoice_id': doc.get('invoice_id'),
            'timestamp': doc.get('timestamp'),
            'total_amount': doc.get('total_amount'),
            'payment_method': doc.get('payment_method'),
            'processed_at': doc.get('processed_at'),
            
            # Complete customer fields
            'customer_id': doc.get('customer', {}).get('customer_id'),
            'customer_first_name': doc.get('customer', {}).get('first_name'),
            'customer_last_name': doc.get('customer', {}).get('last_name'),
            'customer_full_name': f"{doc.get('customer', {}).get('first_name', '')} {doc.get('customer', {}).get('last_name', '')}".strip(),
            'customer_email': doc.get('customer', {}).get('email'),
            'customer_segment': doc.get('customer', {}).get('segment'),
            'customer_loyalty_status': doc.get('customer', {}).get('loyalty_status'),
            'customer_age': doc.get('customer', {}).get('age'),
            
            # Complete store fields
            'store_id': doc.get('store', {}).get('store_id'),
            'store_name': doc.get('store', {}).get('name'),
            'store_city': doc.get('store', {}).get('city'),
            'store_state': doc.get('store', {}).get('state'),
            'store_region': doc.get('store', {}).get('region'),
            'store_location': f"{doc.get('store', {}).get('city', '')}, {doc.get('store', {}).get('state', '')}".strip(', '),
            
            # Calculated fields for analytics
            'invoice_date': doc.get('timestamp', '').split('T')[0] if doc.get('timestamp') else None,
            'invoice_hour': int(doc.get('timestamp', '').split('T')[1].split(':')[0]) if doc.get('timestamp') and 'T' in doc.get('timestamp', '') else None
        })
    return jsonify(data)

@app.route('/health')
def health():
    """Simple health check"""
    try:
        count = db.streaming_invoices.count_documents({})
        return jsonify({'status': 'ok', 'invoices': count})
    except:
        return jsonify({'status': 'error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
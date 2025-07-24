// Initialize MongoDB for invoices
db = db.getSiblingDB('invoices');

// Create streaming invoices collection
db.createCollection('streaming_invoices');

// Create optimized indexes for streaming data
db.streaming_invoices.createIndex({ "invoice_id": 1 }, { unique: true });
db.streaming_invoices.createIndex({ "timestamp": 1 });
db.streaming_invoices.createIndex({ "customer.customer_id": 1 });
db.streaming_invoices.createIndex({ "store.store_id": 1 });
db.streaming_invoices.createIndex({ "total_amount": 1 });

// Create PowerBI user for read-only access
db.createUser({
  user: "powerbi",
  pwd: "powerbi123",
  roles: [{ role: "read", db: "invoices" }]
});

print("MongoDB streaming setup complete!");
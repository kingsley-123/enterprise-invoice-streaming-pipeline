// Initialize MongoDB for invoices
db = db.getSiblingDB('invoices');

// Create main collection
db.createCollection('processed_invoices');

// Create basic indexes
db.processed_invoices.createIndex({ "invoice_id": 1 }, { unique: true });
db.processed_invoices.createIndex({ "timestamp": 1 });

// Create PowerBI user
db.createUser({
  user: "powerbi",
  pwd: "powerbi123",
  roles: [{ role: "read", db: "invoices" }]
});

print("MongoDB setup complete!");
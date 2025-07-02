from fastapi import FastAPI
from typing import Dict, Any
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="Invoice Streaming API", version="1.0.0")

# Simple in-memory storage for testing
invoices_received = []
api_stats = {
    "start_time": datetime.now().isoformat(),
    "total_invoices": 0,
    "total_revenue": 0.0,
    "last_invoice_time": None
}

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Invoice Streaming API",
        "version": "1.0.0",
        "status": "running",
        "total_invoices": len(invoices_received)
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "invoices_received": len(invoices_received),
        "total_revenue": round(api_stats["total_revenue"], 2)
    }

@app.post("/invoices")
def receive_invoice(invoice: Dict[Any, Any]):
    """Receive and store invoice data"""
    # Add timestamp when received
    invoice["api_received_at"] = datetime.now().isoformat()
    
    # Store in memory
    invoices_received.append(invoice)
    
    # Update statistics
    api_stats["total_invoices"] = len(invoices_received)
    api_stats["total_revenue"] += float(invoice.get("total_amount", 0))
    api_stats["last_invoice_time"] = datetime.now().isoformat()
    
    # Log the receipt
    invoice_id = invoice.get("invoice_id", "unknown")
    customer_segment = invoice.get("customer", {}).get("segment", "unknown")
    total_amount = invoice.get("total_amount", 0)
    store_city = invoice.get("store", {}).get("city", "unknown")
    
    print(f"📄 Received: {invoice_id[:8]}... | "
          f"Customer: {customer_segment} | "
          f"Amount: ${total_amount:.2f} | "
          f"Store: {store_city}")
    
    return {
        "status": "received",
        "invoice_id": invoice_id,
        "timestamp": datetime.now().isoformat(),
        "total_invoices": len(invoices_received)
    }

@app.get("/invoices/stats")
def get_stats():
    """Get processing statistics"""
    if not invoices_received:
        return {"message": "No invoices received yet"}
    
    return {
        "total_invoices": len(invoices_received),
        "total_revenue": round(api_stats["total_revenue"], 2),
        "average_amount": round(api_stats["total_revenue"] / len(invoices_received), 2),
        "start_time": api_stats["start_time"],
        "last_invoice": api_stats["last_invoice_time"]
    }

if __name__ == "__main__":
    print("🌟 Starting Invoice Streaming API...")
    print("🔗 API will be available at: http://localhost:8000")
    print("🏥 Health check: http://localhost:8000/health")
    print("📊 Stats: http://localhost:8000/invoices/stats")
    print("📖 Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
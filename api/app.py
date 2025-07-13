from fastapi import FastAPI, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Invoice Streaming API",
    description="Enterprise Invoice Streaming Pipeline API with Data Access",
    version="1.0.0"
)

# Simple in-memory storage for testing
invoices_received = []
api_stats = {
    "start_time": datetime.now().isoformat(),
    "total_invoices": 0,
    "total_revenue": 0.0,
    "last_invoice_time": None
}


# CORE API ENDPOINTS
@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": "Invoice Streaming API",
        "version": "1.0.0",
        "status": "running",
        "total_invoices": len(invoices_received),
        "endpoints": {
            "health": "GET /health",
            "receive_invoice": "POST /invoices",
            "get_all_invoices": "GET /invoices",
            "get_invoice_by_id": "GET /invoices/{invoice_id}",
            "get_latest_invoices": "GET /invoices/latest",
            "get_stats": "GET /invoices/stats",
            "search_invoices": "GET /invoices/search"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    uptime_seconds = (datetime.now() - datetime.fromisoformat(api_stats["start_time"])).total_seconds()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "invoices_received": len(invoices_received),
        "total_revenue": round(api_stats["total_revenue"], 2),
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_minutes": round(uptime_seconds / 60, 2)
    }

@app.post("/invoices")
def receive_invoice(invoice: Dict[Any, Any]):
    """Receive and store invoice data"""
    try:
        # Add API metadata
        invoice["api_received_at"] = datetime.now().isoformat()
        invoice["api_processing_id"] = len(invoices_received) + 1
        
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
            "processing_id": invoice["api_processing_id"],
            "timestamp": datetime.now().isoformat(),
            "total_invoices": len(invoices_received)
        }
        
    except Exception as e:
        print(f"❌ Error processing invoice: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing invoice: {str(e)}")


# DATA ACCESS ENDPOINTS
@app.get("/invoices")
def get_all_invoices(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of invoices to return"),
    offset: int = Query(default=0, ge=0, description="Number of invoices to skip"),
    store_city: Optional[str] = Query(default=None, description="Filter by store city"),
    customer_segment: Optional[str] = Query(default=None, description="Filter by customer segment"),
    min_amount: Optional[float] = Query(default=None, description="Minimum invoice amount"),
    max_amount: Optional[float] = Query(default=None, description="Maximum invoice amount")
):
    """Get invoice data with pagination and filtering"""
    if not invoices_received:
        return {
            "message": "No invoices received yet",
            "total_invoices": 0,
            "returned_count": 0,
            "data": []
        }
    
    # Apply filters
    filtered_invoices = invoices_received.copy()
    
    if store_city:
        filtered_invoices = [inv for inv in filtered_invoices 
                           if inv.get("store", {}).get("city", "").lower() == store_city.lower()]
    
    if customer_segment:
        filtered_invoices = [inv for inv in filtered_invoices 
                           if inv.get("customer", {}).get("segment", "").lower() == customer_segment.lower()]
    
    if min_amount is not None:
        filtered_invoices = [inv for inv in filtered_invoices 
                           if inv.get("total_amount", 0) >= min_amount]
    
    if max_amount is not None:
        filtered_invoices = [inv for inv in filtered_invoices 
                           if inv.get("total_amount", 0) <= max_amount]
    
    # Apply pagination
    start = offset
    end = offset + limit
    invoices_page = filtered_invoices[start:end]
    
    return {
        "total_invoices": len(invoices_received),
        "filtered_count": len(filtered_invoices),
        "returned_count": len(invoices_page),
        "offset": offset,
        "limit": limit,
        "filters": {
            "store_city": store_city,
            "customer_segment": customer_segment,
            "min_amount": min_amount,
            "max_amount": max_amount
        },
        "data": invoices_page
    }

@app.get("/invoices/{invoice_id}")
def get_invoice_by_id(invoice_id: str):
    """Get specific invoice by ID"""
    for invoice in invoices_received:
        if invoice.get('invoice_id') == invoice_id:
            return {
                "found": True,
                "invoice": invoice
            }
    
    raise HTTPException(
        status_code=404, 
        detail=f"Invoice with ID '{invoice_id}' not found"
    )

@app.get("/invoices/latest")
def get_latest_invoices(limit: int = Query(default=10, ge=1, le=100)):
    """Get latest received invoices (simplified view)"""
    if not invoices_received:
        return {
            "message": "No invoices received yet",
            "data": []
        }
    
    # Get latest invoices
    latest = invoices_received[-limit:] if len(invoices_received) >= limit else invoices_received
    
    # Return simplified view
    simplified = []
    for invoice in latest:
        simplified.append({
            "invoice_id": invoice.get("invoice_id", "")[:12] + "...",
            "full_invoice_id": invoice.get("invoice_id", ""),
            "customer_segment": invoice.get("customer", {}).get("segment", "unknown"),
            "customer_name": f"{invoice.get('customer', {}).get('first_name', '')} {invoice.get('customer', {}).get('last_name', '')}",
            "store_city": invoice.get("store", {}).get("city", "unknown"),
            "store_id": invoice.get("store", {}).get("store_id", "unknown"),
            "total_amount": invoice.get("total_amount", 0),
            "item_count": invoice.get("item_count", 0),
            "payment_method": invoice.get("payment_method", "unknown"),
            "timestamp": invoice.get("timestamp", "unknown"),
            "api_received_at": invoice.get("api_received_at", "unknown"),
            "status": invoice.get("status", "unknown")
        })
    
    return {
        "latest_invoices": simplified,
        "count": len(simplified),
        "total_in_system": len(invoices_received)
    }

@app.get("/invoices/search")
def search_invoices(
    q: str = Query(description="Search term"),
    limit: int = Query(default=50, ge=1, le=500)
):
    """Search invoices by various fields"""
    if not invoices_received:
        return {
            "message": "No invoices to search",
            "results": []
        }
    
    search_term = q.lower()
    results = []
    
    for invoice in invoices_received:
        # Search in various fields
        searchable_fields = [
            invoice.get("invoice_id", ""),
            invoice.get("customer", {}).get("first_name", ""),
            invoice.get("customer", {}).get("last_name", ""),
            invoice.get("customer", {}).get("email", ""),
            invoice.get("customer", {}).get("segment", ""),
            invoice.get("store", {}).get("city", ""),
            invoice.get("store", {}).get("name", ""),
            invoice.get("payment_method", ""),
            str(invoice.get("total_amount", ""))
        ]
        
        # Add product names to search
        for item in invoice.get("line_items", []):
            searchable_fields.append(item.get("product", {}).get("name", ""))
            searchable_fields.append(item.get("product", {}).get("category", ""))
        
        # Check if search term matches any field
        if any(search_term in field.lower() for field in searchable_fields):
            results.append(invoice)
            
        if len(results) >= limit:
            break
    
    return {
        "search_term": q,
        "total_matches": len(results),
        "results": results
    }


# ANALYTICS ENDPOINTS
@app.get("/invoices/stats")
def get_detailed_stats():
    """Get detailed processing statistics"""
    if not invoices_received:
        return {"message": "No invoices received yet"}
    
    # Calculate statistics
    segments = {}
    stores = {}
    payment_methods = {}
    categories = {}
    amounts = [inv.get("total_amount", 0) for inv in invoices_received]
    
    for invoice in invoices_received:
        # Customer segments
        segment = invoice.get("customer", {}).get("segment", "unknown")
        segments[segment] = segments.get(segment, 0) + 1
        
        # Stores
        store_city = invoice.get("store", {}).get("city", "unknown")
        stores[store_city] = stores.get(store_city, 0) + 1
        
        # Payment methods
        payment = invoice.get("payment_method", "unknown")
        payment_methods[payment] = payment_methods.get(payment, 0) + 1
        
        # Product categories
        for item in invoice.get("line_items", []):
            category = item.get("product", {}).get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
    
    return {
        "summary": {
            "total_invoices": len(invoices_received),
            "total_revenue": round(api_stats["total_revenue"], 2),
            "average_amount": round(api_stats["total_revenue"] / len(invoices_received), 2),
            "min_amount": round(min(amounts), 2) if amounts else 0,
            "max_amount": round(max(amounts), 2) if amounts else 0,
            "start_time": api_stats["start_time"],
            "last_invoice": api_stats["last_invoice_time"]
        },
        "breakdowns": {
            "customer_segments": segments,
            "top_stores": dict(sorted(stores.items(), key=lambda x: x[1], reverse=True)),
            "payment_methods": payment_methods,
            "product_categories": categories
        }
    }

@app.get("/invoices/analytics/revenue")
def get_revenue_analytics():
    """Get revenue-focused analytics"""
    if not invoices_received:
        return {"message": "No invoices for revenue analysis"}
    
    # Revenue by store
    store_revenue = {}
    segment_revenue = {}
    
    for invoice in invoices_received:
        amount = invoice.get("total_amount", 0)
        store_city = invoice.get("store", {}).get("city", "unknown")
        segment = invoice.get("customer", {}).get("segment", "unknown")
        
        store_revenue[store_city] = store_revenue.get(store_city, 0) + amount
        segment_revenue[segment] = segment_revenue.get(segment, 0) + amount
    
    return {
        "total_revenue": round(sum(store_revenue.values()), 2),
        "revenue_by_store": {k: round(v, 2) for k, v in sorted(store_revenue.items(), key=lambda x: x[1], reverse=True)},
        "revenue_by_segment": {k: round(v, 2) for k, v in sorted(segment_revenue.items(), key=lambda x: x[1], reverse=True)},
        "average_per_store": round(sum(store_revenue.values()) / len(store_revenue), 2) if store_revenue else 0,
        "top_performing_store": max(store_revenue.items(), key=lambda x: x[1])[0] if store_revenue else None
    }


# UTILITY ENDPOINTS
@app.get("/invoices/count")
def get_invoice_count():
    """Simple invoice count"""
    return {
        "total_invoices": len(invoices_received),
        "total_revenue": round(api_stats["total_revenue"], 2),
        "average_amount": round(api_stats["total_revenue"] / len(invoices_received), 2) if invoices_received else 0,
        "last_invoice": api_stats["last_invoice_time"]
    }

@app.delete("/invoices")
def clear_all_invoices():
    """Clear all stored invoices (for testing)"""
    global invoices_received, api_stats
    
    count = len(invoices_received)
    revenue = api_stats["total_revenue"]
    
    invoices_received = []
    api_stats["total_invoices"] = 0
    api_stats["total_revenue"] = 0.0
    api_stats["last_invoice_time"] = None
    
    return {
        "message": "All invoices cleared",
        "cleared_count": count,
        "cleared_revenue": round(revenue, 2),
        "timestamp": datetime.now().isoformat()
    }


# STARTUP MESSAGE
@app.on_event("startup")
async def startup_event():
    print("🚀 Invoice Streaming API Starting...")
    print("📡 Ready to receive invoices at /invoices")
    print("🏥 Health check available at /health")
    print("📊 Statistics available at /invoices/stats")
    print("📄 Get all invoices at /invoices")
    print("🔍 Search invoices at /invoices/search")

# RUN SERVER
if __name__ == "__main__":
    print("🌟 Starting Invoice Streaming API...")
    print("🔗 API will be available at: http://localhost:8000")
    print("🏥 Health check: http://localhost:8000/health")
    print("📊 Stats: http://localhost:8000/invoices/stats")
    print("📄 All invoices: http://localhost:8000/invoices")
    print("🔍 Search: http://localhost:8000/invoices/search?q=premium")
    print("📖 Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
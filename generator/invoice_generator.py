#!/usr/bin/env python3
"""
Enterprise Invoice Data Generator for Real-Time Streaming Pipeline
Generates realistic e-commerce invoices at enterprise scale (2.9M/day capacity)
"""

import uuid
import random
import json
import time
import argparse
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import faker
import requests
import threading
from concurrent.futures import ThreadPoolExecutor

# Initialize faker for realistic data
fake = faker.Faker()

# =============================================================================
# REFERENCE DATA - Enterprise Business Logic
# =============================================================================

# Store locations across different regions
STORES = [
    {"store_id": "NYC-001", "name": "Manhattan Downtown", "city": "New York", "state": "NY", "region": "Northeast"},
    {"store_id": "LA-001", "name": "Hollywood Boulevard", "city": "Los Angeles", "state": "CA", "region": "West"},
    {"store_id": "CHI-001", "name": "Magnificent Mile", "city": "Chicago", "state": "IL", "region": "Midwest"},
    {"store_id": "MIA-001", "name": "South Beach", "city": "Miami", "state": "FL", "region": "Southeast"},
    {"store_id": "SEA-001", "name": "Pike Place", "city": "Seattle", "state": "WA", "region": "Northwest"},
    {"store_id": "DAL-001", "name": "Deep Ellum", "city": "Dallas", "state": "TX", "region": "Southwest"},
    {"store_id": "BOS-001", "name": "Back Bay", "city": "Boston", "state": "MA", "region": "Northeast"},
    {"store_id": "SF-001", "name": "Union Square", "city": "San Francisco", "state": "CA", "region": "West"},
    {"store_id": "ATL-001", "name": "Buckhead", "city": "Atlanta", "state": "GA", "region": "Southeast"},
    {"store_id": "DEN-001", "name": "Downtown", "city": "Denver", "state": "CO", "region": "Southwest"}
]

# Payment methods with realistic usage weights
PAYMENT_METHODS = [
    {"method": "credit_card", "type": "Visa", "weight": 45},
    {"method": "credit_card", "type": "Mastercard", "weight": 30},
    {"method": "credit_card", "type": "American Express", "weight": 15},
    {"method": "debit_card", "type": "Visa Debit", "weight": 25},
    {"method": "digital_wallet", "type": "Apple Pay", "weight": 20},
    {"method": "digital_wallet", "type": "Google Pay", "weight": 15},
    {"method": "digital_wallet", "type": "PayPal", "weight": 10},
    {"method": "cash", "type": "Cash", "weight": 8},
    {"method": "buy_now_pay_later", "type": "Klarna", "weight": 5}
]

# Customer segments with different behaviors
CUSTOMER_SEGMENTS = [
    {"segment": "Premium", "avg_order": 450, "weight": 15},
    {"segment": "Regular", "avg_order": 150, "weight": 60},
    {"segment": "Budget", "avg_order": 75, "weight": 20},
    {"segment": "New", "avg_order": 120, "weight": 5}
]

# Products with realistic pricing
PRODUCTS = [
    {"id": "ELEC-001", "name": "iPhone 15 Pro", "category": "Electronics", "price": 999.00, "weight": 10},
    {"id": "ELEC-002", "name": "Samsung Galaxy S24", "category": "Electronics", "price": 849.00, "weight": 8},
    {"id": "ELEC-003", "name": "MacBook Air M3", "category": "Electronics", "price": 1299.00, "weight": 5},
    {"id": "ELEC-004", "name": "Sony Headphones", "category": "Electronics", "price": 299.00, "weight": 15},
    {"id": "CLTH-001", "name": "Nike Air Max", "category": "Clothing", "price": 150.00, "weight": 20},
    {"id": "CLTH-002", "name": "Levi's Jeans", "category": "Clothing", "price": 89.00, "weight": 25},
    {"id": "CLTH-003", "name": "North Face Jacket", "category": "Clothing", "price": 199.00, "weight": 12},
    {"id": "HOME-001", "name": "KitchenAid Mixer", "category": "Home", "price": 349.00, "weight": 8},
    {"id": "HOME-002", "name": "Dyson Vacuum", "category": "Home", "price": 649.00, "weight": 6},
    {"id": "BEAU-001", "name": "Skincare Set", "category": "Beauty", "price": 45.00, "weight": 30}
]

# =============================================================================
# DATA CLASSES - Invoice Structure
# =============================================================================

@dataclass
class Customer:
    customer_id: str
    first_name: str
    last_name: str
    email: str
    segment: str
    loyalty_status: str
    age: int

@dataclass
class Store:
    store_id: str
    name: str
    city: str
    state: str
    region: str

@dataclass
class Product:
    product_id: str
    name: str
    category: str
    price: float

@dataclass
class LineItem:
    product: Product
    quantity: int
    unit_price: float
    line_total: float

@dataclass
class Invoice:
    # Core fields
    invoice_id: str
    invoice_number: str
    timestamp: str
    
    # Business entities
    customer: Customer
    store: Store
    line_items: List[LineItem]
    
    # Financial
    subtotal: float
    tax_amount: float
    total_amount: float
    
    # Payment
    payment_method: str
    payment_type: str
    
    # Analytics
    item_count: int
    total_quantity: int
    profit_margin: float
    is_weekend: bool
    season: str
    
    # Status
    status: str

# =============================================================================
# INVOICE GENERATOR CLASS
# =============================================================================

class EnterpriseInvoiceGenerator:
    """Enterprise-grade invoice generator for streaming pipeline"""
    
    def __init__(self):
        self.customer_database = self._create_customer_base()
        self.stats = {
            'invoices_generated': 0,
            'total_revenue': 0.0,
            'start_time': None
        }
    
    def _create_customer_base(self) -> Dict[str, Dict]:
        """Create realistic customer database"""
        customers = {}
        for i in range(10000):  # 10k existing customers
            customer_id = f"CUST-{i:06d}"
            segment = self._weighted_choice(CUSTOMER_SEGMENTS)['segment']
            
            customers[customer_id] = {
                'segment': segment,
                'loyalty_status': random.choice(['None', 'Bronze', 'Silver', 'Gold', 'Platinum']),
                'order_count': random.randint(1, 50),
                'last_order': fake.date_between(start_date='-1y', end_date='today')
            }
        return customers
    
    def _weighted_choice(self, items: List[Dict]) -> Dict:
        """Select item based on weight"""
        weights = [item['weight'] for item in items]
        return random.choices(items, weights=weights, k=1)[0]
    
    def _generate_customer(self) -> Customer:
        """Generate customer (80% returning, 20% new)"""
        is_returning = random.random() < 0.8
        
        if is_returning and self.customer_database:
            customer_id = random.choice(list(self.customer_database.keys()))
            customer_data = self.customer_database[customer_id]
            segment = customer_data['segment']
            loyalty = customer_data['loyalty_status']
        else:
            customer_id = f"CUST-{random.randint(100000, 999999)}"
            segment = self._weighted_choice(CUSTOMER_SEGMENTS)['segment']
            loyalty = random.choice(['None', 'Bronze', 'Silver'])
        
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        return Customer(
            customer_id=customer_id,
            first_name=first_name,
            last_name=last_name,
            email=f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}",
            segment=segment,
            loyalty_status=loyalty,
            age=random.randint(18, 75)
        )
    
    def _generate_line_items(self, customer_segment: str) -> List[LineItem]:
        """Generate line items based on customer behavior"""
        # Different segments buy different amounts
        item_counts = {
            'Premium': (1, 4),
            'Regular': (1, 3),
            'Budget': (1, 2),
            'New': (1, 2)
        }
        
        min_items, max_items = item_counts[customer_segment]
        num_items = random.randint(min_items, max_items)
        
        line_items = []
        used_products = set()
        
        for _ in range(num_items):
            # Avoid duplicate products
            available_products = [p for p in PRODUCTS if p['id'] not in used_products]
            if not available_products:
                break
                
            product_data = self._weighted_choice(available_products)
            used_products.add(product_data['id'])
            
            product = Product(
                product_id=product_data['id'],
                name=product_data['name'],
                category=product_data['category'],
                price=product_data['price']
            )
            
            quantity = random.randint(1, 3)
            unit_price = product.price
            
            # Apply small random price variations (sales, etc)
            price_variation = random.uniform(0.9, 1.1)
            unit_price = round(unit_price * price_variation, 2)
            
            line_total = round(unit_price * quantity, 2)
            
            line_items.append(LineItem(
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total
            ))
        
        return line_items
    
    def _calculate_finances(self, line_items: List[LineItem]) -> tuple:
        """Calculate financial totals"""
        subtotal = sum(item.line_total for item in line_items)
        tax_rate = 0.0875  # 8.75% tax
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = round(subtotal + tax_amount, 2)
        
        # Simple profit margin calculation (30% average)
        profit_margin = round(random.uniform(25.0, 35.0), 2)
        
        return subtotal, tax_amount, total_amount, profit_margin
    
    def _get_season(self, date: datetime) -> str:
        """Determine season from date"""
        month = date.month
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
    
    def generate_invoice(self) -> Invoice:
        """Generate a single realistic invoice"""
        timestamp = datetime.now()
        
        # Generate components
        customer = self._generate_customer()
        store_data = self._weighted_choice(STORES)
        store = Store(**store_data)
        line_items = self._generate_line_items(customer.segment)
        
        # Calculate finances
        subtotal, tax_amount, total_amount, profit_margin = self._calculate_finances(line_items)
        
        # Payment method
        payment_data = self._weighted_choice(PAYMENT_METHODS)
        
        # Create invoice
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            invoice_number=f"INV-{timestamp.strftime('%Y%m%d')}-{random.randint(1000, 9999)}",
            timestamp=timestamp.isoformat(),
            
            customer=customer,
            store=store,
            line_items=line_items,
            
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            
            payment_method=payment_data['method'],
            payment_type=payment_data['type'],
            
            item_count=len(line_items),
            total_quantity=sum(item.quantity for item in line_items),
            profit_margin=profit_margin,
            is_weekend=timestamp.weekday() >= 5,
            season=self._get_season(timestamp),
            
            status=random.choices(
                ['completed', 'pending', 'failed'],
                weights=[85, 10, 5]
            )[0]
        )
        
        # Update stats
        self.stats['invoices_generated'] += 1
        self.stats['total_revenue'] += total_amount
        
        return invoice
    
    def generate_batch(self, batch_size: int = 100) -> List[Dict]:
        """Generate batch of invoices for streaming"""
        invoices = []
        for _ in range(batch_size):
            invoice = self.generate_invoice()
            invoice_dict = asdict(invoice)
            invoices.append(invoice_dict)
        
        return invoices
    
    def start_streaming(self, rate_per_minute: int = 100, 
                       duration_minutes: int = None,
                       api_endpoint: str = None) -> None:
        """Start continuous invoice generation for streaming pipeline"""
        
        print(f"🚀 Starting invoice generation at {rate_per_minute} invoices/minute")
        if duration_minutes:
            print(f"⏱️  Running for {duration_minutes} minutes")
        if api_endpoint:
            print(f"📡 Sending to API: {api_endpoint}")
        
        self.stats['start_time'] = datetime.now()
        
        # Calculate timing
        interval_seconds = 60.0 / rate_per_minute
        end_time = None
        if duration_minutes:
            end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        try:
            while True:
                start_time = time.time()
                
                # Check if we should stop
                if end_time and datetime.now() >= end_time:
                    break
                
                # Generate invoice
                invoice = self.generate_invoice()
                
                # Send to API if endpoint provided
                if api_endpoint:
                    self._send_to_api(invoice, api_endpoint)
                else:
                    # Just print to console for testing
                    print(f"📄 Generated: {invoice.invoice_id} | "
                          f"Customer: {invoice.customer.segment} | "
                          f"Total: ${invoice.total_amount:.2f} | "
                          f"Store: {invoice.store.city}")
                
                # Print stats every 100 invoices
                if self.stats['invoices_generated'] % 100 == 0:
                    self._print_stats()
                
                # Sleep for precise timing
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\n⏹️  Generation stopped by user")
        finally:
            self._print_final_stats()
    
    def _send_to_api(self, invoice: Invoice, endpoint: str) -> None:
        """Send invoice to API endpoint"""
        try:
            invoice_dict = asdict(invoice)
            response = requests.post(
                endpoint,
                json=invoice_dict,
                timeout=5,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                print(f"⚠️  API Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send to API: {e}")
    
    def _print_stats(self) -> None:
        """Print current generation statistics"""
        if not self.stats['start_time']:
            return
            
        elapsed = datetime.now() - self.stats['start_time']
        elapsed_minutes = elapsed.total_seconds() / 60
        
        if elapsed_minutes > 0:
            rate = self.stats['invoices_generated'] / elapsed_minutes
            avg_revenue = self.stats['total_revenue'] / self.stats['invoices_generated']
            
            print(f"📊 Stats: {self.stats['invoices_generated']:,} invoices | "
                  f"Rate: {rate:.1f}/min | "
                  f"Revenue: ${self.stats['total_revenue']:,.2f} | "
                  f"Avg: ${avg_revenue:.2f}")
    
    def _print_final_stats(self) -> None:
        """Print final generation statistics"""
        print(f"\n📈 Final Statistics:")
        print(f"  Invoices Generated: {self.stats['invoices_generated']:,}")
        print(f"  Total Revenue: ${self.stats['total_revenue']:,.2f}")
        
        if self.stats['start_time']:
            elapsed = datetime.now() - self.stats['start_time']
            elapsed_minutes = elapsed.total_seconds() / 60
            if elapsed_minutes > 0:
                rate = self.stats['invoices_generated'] / elapsed_minutes
                print(f"  Average Rate: {rate:.1f} invoices/minute")
                print(f"  Duration: {elapsed_minutes:.1f} minutes")

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Enterprise Invoice Data Generator')
    parser.add_argument('--rate', type=int, default=100,
                       help='Invoices per minute (default: 100)')
    parser.add_argument('--duration', type=int, default=None,
                       help='Duration in minutes (default: unlimited)')
    parser.add_argument('--batch-size', type=int, default=None,
                       help='Generate single batch and exit')
    parser.add_argument('--api-endpoint', type=str, default=None,
                       help='API endpoint to send invoices (e.g., http://localhost:8000/invoices)')
    parser.add_argument('--output-file', type=str, default=None,
                       help='Save invoices to JSON file instead of streaming')
    parser.add_argument('--test', action='store_true',
                       help='Generate single test invoice and exit')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = EnterpriseInvoiceGenerator()
    
    if args.test:
        # Generate single test invoice
        print("🧪 Generating test invoice...")
        invoice = generator.generate_invoice()
        invoice_json = json.dumps(asdict(invoice), indent=2, default=str)
        print(invoice_json)
        return
    
    if args.batch_size:
        # Generate single batch
        print(f"📦 Generating batch of {args.batch_size} invoices...")
        batch = generator.generate_batch(args.batch_size)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(batch, f, indent=2, default=str)
            print(f"💾 Saved {len(batch)} invoices to {args.output_file}")
        else:
            print(f"Generated {len(batch)} invoices")
            print("Sample invoice:")
            print(json.dumps(batch[0], indent=2, default=str)[:500] + "...")
        return
    
    # Start continuous streaming
    generator.start_streaming(
        rate_per_minute=args.rate,
        duration_minutes=args.duration,
        api_endpoint=args.api_endpoint
    )

main()
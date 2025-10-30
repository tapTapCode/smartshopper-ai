"""Sample product data for SmartShopper AI."""

from typing import List
from datetime import datetime
import asyncio

from .models import Product, ProductCategory
from .search import search_service


def create_sample_products() -> List[Product]:
    """Create sample products for testing."""
    products = [
        # Electronics
        Product(
            id="1",
            name="iPhone 15 Pro",
            description="Latest iPhone with A17 Pro chip, titanium design, and advanced camera system",
            category=ProductCategory.ELECTRONICS,
            price=999.00,
            brand="Apple",
            model="iPhone 15 Pro",
            sku="IPHONE15PRO",
            features=[
                "A17 Pro chip",
                "Triple camera system",
                "Titanium design",
                "USB-C connector",
                "Action button"
            ],
            specifications={
                "screen_size": "6.1 inches",
                "storage": "128GB",
                "ram": "8GB",
                "camera": "48MP main",
                "battery": "3274mAh"
            },
            tags=["smartphone", "apple", "premium", "latest"],
            in_stock=True,
            stock_quantity=50,
            rating=4.8,
            review_count=1250,
            product_url="https://example.com/iphone-15-pro"
        ),
        Product(
            id="2",
            name="MacBook Air M3",
            description="Lightweight laptop with M3 chip, perfect for everyday computing",
            category=ProductCategory.ELECTRONICS,
            price=1099.00,
            brand="Apple",
            model="MacBook Air M3",
            sku="MACBOOKAIR-M3",
            features=[
                "M3 chip",
                "13.6-inch Liquid Retina display",
                "8-core CPU",
                "10-core GPU",
                "18-hour battery life"
            ],
            specifications={
                "screen_size": "13.6 inches",
                "processor": "Apple M3",
                "ram": "8GB",
                "storage": "256GB SSD",
                "weight": "2.7 lbs"
            },
            tags=["laptop", "apple", "lightweight", "productivity"],
            in_stock=True,
            stock_quantity=30,
            rating=4.7,
            review_count=890,
            product_url="https://example.com/macbook-air-m3"
        ),
        Product(
            id="3",
            name="Sony WH-1000XM5 Headphones",
            description="Industry-leading noise canceling wireless headphones",
            category=ProductCategory.ELECTRONICS,
            price=399.99,
            brand="Sony",
            model="WH-1000XM5",
            sku="SONY-WH1000XM5",
            features=[
                "Industry-leading noise canceling",
                "30-hour battery life",
                "Quick charge",
                "High-resolution audio",
                "Touch controls"
            ],
            specifications={
                "battery_life": "30 hours",
                "charging_time": "3 hours",
                "weight": "8.8 oz",
                "connectivity": "Bluetooth 5.2",
                "frequency_response": "4Hz-40kHz"
            },
            tags=["headphones", "wireless", "noise-canceling", "premium"],
            in_stock=True,
            stock_quantity=75,
            rating=4.6,
            review_count=2100,
            product_url="https://example.com/sony-wh1000xm5"
        ),
        
        # Clothing
        Product(
            id="4",
            name="Levi's 501 Original Jeans",
            description="Classic straight-leg jeans with authentic fit and timeless style",
            category=ProductCategory.CLOTHING,
            price=69.50,
            brand="Levi's",
            model="501 Original",
            sku="LEVIS-501-BLUE",
            features=[
                "100% cotton denim",
                "Straight leg fit",
                "Button fly",
                "Classic 5-pocket styling",
                "Shrink-to-fit"
            ],
            specifications={
                "material": "100% Cotton",
                "fit": "Straight",
                "rise": "Mid",
                "leg_opening": "16 inches",
                "inseam": "32 inches"
            },
            tags=["jeans", "denim", "classic", "casual"],
            in_stock=True,
            stock_quantity=120,
            rating=4.4,
            review_count=5600,
            product_url="https://example.com/levis-501-jeans"
        ),
        
        # Home & Garden
        Product(
            id="5",
            name="Instant Pot Duo 7-in-1",
            description="Multi-functional electric pressure cooker for quick, easy, and healthy meals",
            category=ProductCategory.HOME,
            price=89.95,
            brand="Instant Pot",
            model="Duo 7-in-1",
            sku="INSTANTPOT-DUO7",
            features=[
                "7 appliances in 1",
                "6-quart capacity",
                "14 smart programs",
                "Safe and convenient",
                "Dishwasher safe"
            ],
            specifications={
                "capacity": "6 quarts",
                "programs": "14 smart programs",
                "pressure_cooking": "Yes",
                "slow_cooking": "Yes",
                "dimensions": "13.4 x 12.4 x 12.8 inches"
            },
            tags=["kitchen", "pressure-cooker", "multi-cooker", "appliance"],
            in_stock=True,
            stock_quantity=85,
            rating=4.5,
            review_count=15600,
            product_url="https://example.com/instant-pot-duo"
        ),
        
        # Books
        Product(
            id="6",
            name="The Pragmatic Programmer",
            description="Classic guide to software development best practices and craftsmanship",
            category=ProductCategory.BOOKS,
            price=49.95,
            brand="Addison-Wesley",
            model="20th Anniversary Edition",
            sku="PRAGPROG-20TH",
            features=[
                "Updated for 2020",
                "New content on modern practices",
                "Timeless principles",
                "Practical examples",
                "Industry standard"
            ],
            specifications={
                "pages": "352",
                "publisher": "Addison-Wesley Professional",
                "edition": "2nd Edition",
                "language": "English",
                "isbn": "978-0135957059"
            },
            tags=["programming", "software-development", "technical", "reference"],
            in_stock=True,
            stock_quantity=200,
            rating=4.7,
            review_count=1890,
            product_url="https://example.com/pragmatic-programmer"
        ),
        
        # Sports & Outdoors
        Product(
            id="7",
            name="Nike Air Max 270",
            description="Lifestyle shoe with Max Air unit for all-day comfort",
            category=ProductCategory.SPORTS,
            price=149.97,
            brand="Nike",
            model="Air Max 270",
            sku="NIKE-AIRMAX270",
            features=[
                "Max Air unit",
                "Breathable mesh upper",
                "Foam midsole",
                "Rubber outsole",
                "Lifestyle design"
            ],
            specifications={
                "upper_material": "Mesh and synthetic",
                "midsole": "Foam with Max Air unit",
                "outsole": "Rubber",
                "weight": "13.6 oz",
                "heel_drop": "12mm"
            },
            tags=["sneakers", "lifestyle", "comfortable", "athletic"],
            in_stock=True,
            stock_quantity=95,
            rating=4.3,
            review_count=3200,
            product_url="https://example.com/nike-air-max-270"
        ),
        
        # Beauty
        Product(
            id="8",
            name="CeraVe Daily Moisturizing Lotion",
            description="Lightweight, oil-free moisturizer for normal to dry skin",
            category=ProductCategory.BEAUTY,
            price=16.49,
            brand="CeraVe",
            model="Daily Moisturizing Lotion",
            sku="CERAVE-DAILY-LOTION",
            features=[
                "3 essential ceramides",
                "Hyaluronic acid",
                "MVE technology",
                "Non-greasy formula",
                "Fragrance-free"
            ],
            specifications={
                "size": "19 fl oz",
                "skin_type": "Normal to dry",
                "spf": "None",
                "ingredients": "Ceramides, Hyaluronic Acid",
                "cruelty_free": "Yes"
            },
            tags=["skincare", "moisturizer", "daily", "sensitive-skin"],
            in_stock=True,
            stock_quantity=150,
            rating=4.6,
            review_count=8900,
            product_url="https://example.com/cerave-daily-lotion"
        )
    ]
    
    return products


async def index_sample_data():
    """Index sample products into Elasticsearch."""
    try:
        print("Creating sample products...")
        products = create_sample_products()
        
        print("Ensuring Elasticsearch index exists...")
        await search_service.ensure_index_exists()
        
        print(f"Indexing {len(products)} sample products...")
        success_count = await search_service.index_products(products)
        
        print(f"Successfully indexed {success_count} products")
        return success_count
        
    except Exception as e:
        print(f"Error indexing sample data: {e}")
        return 0


if __name__ == "__main__":
    # Run the indexing script
    asyncio.run(index_sample_data())
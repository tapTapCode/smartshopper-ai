"""Unit tests for AIService."""

import pytest
from src.ai_service import AIService
from src.models import Product, ProductCategory
from datetime import datetime


@pytest.fixture
def ai_service():
    """Create AIService instance for testing."""
    return AIService()


@pytest.fixture
def sample_products():
    """Create sample products for testing."""
    return [
        Product(
            id="1",
            name="iPhone 14 Pro",
            description="Latest Apple smartphone",
            category=ProductCategory.ELECTRONICS,
            price=999.99,
            brand="Apple",
            rating=4.8,
            in_stock=True
        ),
        Product(
            id="2",
            name="Sony WH-1000XM5",
            description="Premium noise canceling headphones",
            category=ProductCategory.ELECTRONICS,
            price=399.99,
            brand="Sony",
            rating=4.7,
            in_stock=True
        ),
        Product(
            id="3",
            name="MacBook Pro M2",
            description="Powerful laptop for professionals",
            category=ProductCategory.ELECTRONICS,
            price=1999.99,
            brand="Apple",
            rating=4.9,
            in_stock=True
        )
    ]


class TestExtractSearchTerms:
    """Tests for AIService._extract_search_terms method."""
    
    def test_extract_category_phone(self, ai_service):
        """Test extraction of phone category keyword."""
        message = "I'm looking for a new phone"
        result = ai_service._extract_search_terms(message)
        assert result == "smartphone"
    
    def test_extract_category_laptop(self, ai_service):
        """Test extraction of laptop category keyword."""
        message = "Need a laptop for work"
        result = ai_service._extract_search_terms(message)
        assert result == "laptop"
    
    def test_extract_category_headphones(self, ai_service):
        """Test extraction of headphones category keyword."""
        message = "Looking for headphones"
        result = ai_service._extract_search_terms(message)
        assert result == "headphones"
    
    def test_extract_category_jeans(self, ai_service):
        """Test extraction of jeans category keyword."""
        message = "I need new jeans"
        result = ai_service._extract_search_terms(message)
        assert result == "jeans"
    
    def test_extract_category_cooking(self, ai_service):
        """Test extraction of cooking/kitchen category keyword."""
        message = "Looking for cooking equipment"
        result = ai_service._extract_search_terms(message)
        assert result == "kitchen"
    
    def test_extract_category_book(self, ai_service):
        """Test extraction of book/programming category keyword."""
        message = "I want to buy a programming book"
        result = ai_service._extract_search_terms(message)
        assert result == "programming"
    
    def test_extract_brand_apple(self, ai_service):
        """Test extraction of Apple brand keyword."""
        message = "Show me Apple products"
        result = ai_service._extract_search_terms(message)
        assert result == "apple"
    
    def test_extract_brand_iphone(self, ai_service):
        """Test extraction of iPhone brand keyword."""
        message = "I want an iPhone"
        result = ai_service._extract_search_terms(message)
        assert result == "iphone"
    
    def test_extract_brand_sony(self, ai_service):
        """Test extraction of Sony brand keyword."""
        message = "Looking for Sony headphones"
        result = ai_service._extract_search_terms(message)
        assert result == "sony"
    
    def test_extract_brand_nike(self, ai_service):
        """Test extraction of Nike brand keyword."""
        message = "Need Nike shoes"
        result = ai_service._extract_search_terms(message)
        assert result == "nike"
    
    def test_extract_brand_case_insensitive(self, ai_service):
        """Test brand extraction is case insensitive."""
        message = "I want APPLE products"
        result = ai_service._extract_search_terms(message)
        assert result == "apple"
    
    def test_extract_price_budget(self, ai_service):
        """Test extraction of budget price keyword."""
        message = "Show me cheap products"
        result = ai_service._extract_search_terms(message)
        assert result == "budget"
    
    def test_extract_price_affordable(self, ai_service):
        """Test extraction of affordable price keyword."""
        message = "Looking for affordable options"
        result = ai_service._extract_search_terms(message)
        assert result == "budget"
    
    def test_extract_price_under(self, ai_service):
        """Test extraction of under price keyword."""
        message = "Products under $100"
        result = ai_service._extract_search_terms(message)
        assert result == "budget"
    
    def test_extract_price_premium(self, ai_service):
        """Test extraction of premium price keyword."""
        message = "Show me premium laptops"
        result = ai_service._extract_search_terms(message)
        assert result == "premium"
    
    def test_extract_price_expensive(self, ai_service):
        """Test extraction of expensive price keyword."""
        message = "I want expensive headphones"
        result = ai_service._extract_search_terms(message)
        assert result == "premium"
    
    def test_extract_price_high_end(self, ai_service):
        """Test extraction of high-end price keyword."""
        message = "Looking for high-end electronics"
        result = ai_service._extract_search_terms(message)
        assert result == "premium"
    
    def test_extract_long_message(self, ai_service):
        """Test extraction from long message filters key words."""
        message = "I am looking for a very good quality product that can help me with my daily work and should not be too expensive"
        result = ai_service._extract_search_terms(message)
        # Should extract key words and limit to 5
        assert len(result.split()) <= 5
        assert "looking" in result
        assert "quality" in result
        assert "product" in result
    
    def test_extract_short_message_cleaned(self, ai_service):
        """Test extraction from short message cleans punctuation."""
        message = "What is the best laptop?"
        result = ai_service._extract_search_terms(message)
        # Should match laptop first
        assert result == "laptop"
    
    def test_extract_generic_message(self, ai_service):
        """Test extraction from generic message returns cleaned text."""
        message = "Cool stuff!"
        result = ai_service._extract_search_terms(message)
        assert result == "Cool stuff"  # Cleaned punctuation


class TestGenerateFallbackResponse:
    """Tests for AIService._generate_fallback_response method."""
    
    def test_fallback_with_single_product(self, ai_service, sample_products):
        """Test fallback response with single product."""
        products = [sample_products[0]]
        result = ai_service._generate_fallback_response("Looking for a phone", products)
        
        assert "iPhone 14 Pro" in result
        assert "Apple" in result
        assert "999.99" in result
        assert "4.8" in result
        assert "in stock" in result.lower()
    
    def test_fallback_with_multiple_products(self, ai_service, sample_products):
        """Test fallback response with multiple products."""
        result = ai_service._generate_fallback_response("Show me electronics", sample_products)
        
        assert f"{len(sample_products)} great options" in result
        assert "iPhone 14 Pro" in result  # Top product
        assert "Apple" in result
        assert "999.99" in result
        assert "more details" in result.lower() or "filter" in result.lower()
    
    def test_fallback_no_products_greeting(self, ai_service):
        """Test fallback response with no products and greeting."""
        result = ai_service._generate_fallback_response("Hello", [])
        
        assert "hello" in result.lower() or "hi" in result.lower()
        assert "smartshopper ai" in result.lower()
        assert "shopping assistant" in result.lower()
    
    def test_fallback_no_products_hi(self, ai_service):
        """Test fallback response with no products and hi greeting."""
        result = ai_service._generate_fallback_response("Hi there", [])
        
        assert "hello" in result.lower() or "hi" in result.lower()
        assert "smartshopper ai" in result.lower()
    
    def test_fallback_no_products_help(self, ai_service):
        """Test fallback response with no products and help request."""
        result = ai_service._generate_fallback_response("help me", [])
        
        assert "help" in result.lower()
        assert "categories" in result.lower() or "electronics" in result.lower()
        assert "budget" in result.lower() or "preferences" in result.lower()
    
    def test_fallback_no_products_what_can_you_do(self, ai_service):
        """Test fallback response with no products and capability question."""
        result = ai_service._generate_fallback_response("What can you do?", [])
        
        assert "help" in result.lower() or "find" in result.lower()
        assert "products" in result.lower()
    
    def test_fallback_no_products_generic(self, ai_service):
        """Test fallback response with no products and generic message."""
        result = ai_service._generate_fallback_response("Show me something", [])
        
        assert "couldn't find" in result.lower() or "no products" in result.lower()
        assert "help" in result.lower()
        assert "budget" in result.lower() or "preferences" in result.lower()
    
    def test_fallback_preserves_product_details(self, ai_service):
        """Test fallback response includes all key product details."""
        product = Product(
            id="test1",
            name="Test Product",
            description="Test description",
            category=ProductCategory.ELECTRONICS,
            price=199.99,
            brand="TestBrand",
            rating=4.5,
            in_stock=True
        )
        result = ai_service._generate_fallback_response("test", [product])
        
        assert "Test Product" in result
        assert "TestBrand" in result
        assert "199.99" in result
        assert "4.5" in result


class TestGenerateSuggestions:
    """Tests for AIService._generate_suggestions method."""
    
    def test_suggestions_with_electronics_products(self, ai_service, sample_products):
        """Test suggestions generation with electronics products."""
        result = ai_service._generate_suggestions("Show me phones", sample_products)
        
        assert len(result) <= 3  # Limited to 3 suggestions
        assert any("electronics" in s.lower() for s in result)
        assert any("compare" in s.lower() or "budget" in s.lower() or "premium" in s.lower() for s in result)
    
    def test_suggestions_with_price_based_filters(self, ai_service, sample_products):
        """Test suggestions include price-based filters."""
        result = ai_service._generate_suggestions("Electronics", sample_products)
        
        # Should suggest price filters based on average
        assert any("under" in s.lower() or "$" in s for s in result)
        assert any("above" in s.lower() or "premium" in s.lower() for s in result)
    
    def test_suggestions_without_products(self, ai_service):
        """Test suggestions when no products found."""
        result = ai_service._generate_suggestions("Random query", [])
        
        assert len(result) <= 3
        assert any("browse" in s.lower() or "popular" in s.lower() for s in result)
        assert any("deals" in s.lower() or "discounts" in s.lower() for s in result)
        assert any("help" in s.lower() or "specific" in s.lower() or "trending" in s.lower() for s in result)
    
    def test_suggestions_no_products_general(self, ai_service):
        """Test suggestions provide general browsing options without products."""
        result = ai_service._generate_suggestions("test", [])
        
        # Should include general suggestions
        suggestion_text = " ".join(result).lower()
        assert "browse" in suggestion_text or "popular" in suggestion_text
        assert "deals" in suggestion_text or "trending" in suggestion_text
    
    def test_suggestions_limited_to_three(self, ai_service, sample_products):
        """Test suggestions are limited to maximum of 3."""
        result = ai_service._generate_suggestions("Show me products", sample_products)
        assert len(result) <= 3
    
    def test_suggestions_single_product(self, ai_service):
        """Test suggestions with single product."""
        product = Product(
            id="1",
            name="Test Product",
            description="Test",
            category=ProductCategory.ELECTRONICS,
            price=100.0,
            brand="Test"
        )
        result = ai_service._generate_suggestions("test", [product])
        
        assert len(result) <= 3
        # Should still provide useful suggestions
        assert len(result) > 0
    
    def test_suggestions_mixed_categories(self, ai_service):
        """Test suggestions with products from different categories."""
        products = [
            Product(
                id="1",
                name="Phone",
                description="Test",
                category=ProductCategory.ELECTRONICS,
                price=500.0,
                brand="Test"
            ),
            Product(
                id="2",
                name="Shirt",
                description="Test",
                category=ProductCategory.CLOTHING,
                price=50.0,
                brand="Test"
            )
        ]
        result = ai_service._generate_suggestions("products", products)
        
        assert len(result) <= 3
        # Should focus on electronics if present
        assert any("electronics" in s.lower() for s in result)
    
    def test_suggestions_relevant_to_context(self, ai_service, sample_products):
        """Test suggestions are contextually relevant to products."""
        result = ai_service._generate_suggestions("Apple products", sample_products)
        
        # With electronics products, should suggest relevant actions
        suggestion_text = " ".join(result).lower()
        assert any(keyword in suggestion_text for keyword in ["electronics", "compare", "budget", "premium", "under", "above"])

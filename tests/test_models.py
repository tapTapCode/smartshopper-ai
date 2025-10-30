"""Tests for Pydantic data models."""

import pytest
from pydantic import ValidationError
from datetime import datetime
from src.models import (
    Product, ProductCategory, SearchRequest, SearchResponse,
    ChatMessage, ChatResponse, HealthStatus
)


def test_product_model_valid():
    """Test Product model with valid data."""
    product = Product(
        id="test-1",
        name="Test Product",
        description="A test product",
        category=ProductCategory.ELECTRONICS,
        price=99.99,
        brand="TestBrand"
    )
    
    assert product.id == "test-1"
    assert product.name == "Test Product"
    assert product.category == ProductCategory.ELECTRONICS
    assert product.price == 99.99
    assert product.currency == "USD"  # default value
    assert product.in_stock == True  # default value


def test_product_model_invalid_price():
    """Test Product model with invalid price."""
    with pytest.raises(ValidationError):
        Product(
            id="test-1",
            name="Test Product",
            description="A test product",
            category=ProductCategory.ELECTRONICS,
            price=-10.0  # Invalid negative price
        )


def test_product_model_invalid_rating():
    """Test Product model with invalid rating."""
    with pytest.raises(ValidationError):
        Product(
            id="test-1",
            name="Test Product",
            description="A test product",
            category=ProductCategory.ELECTRONICS,
            price=99.99,
            rating=6.0  # Invalid rating > 5
        )


def test_search_request_model():
    """Test SearchRequest model."""
    search_req = SearchRequest(
        query="laptop",
        category=ProductCategory.ELECTRONICS,
        min_price=500.0,
        max_price=2000.0,
        page=1,
        page_size=20
    )
    
    assert search_req.query == "laptop"
    assert search_req.category == ProductCategory.ELECTRONICS
    assert search_req.min_price == 500.0
    assert search_req.max_price == 2000.0
    assert search_req.in_stock_only == True  # default


def test_search_request_invalid_page():
    """Test SearchRequest with invalid page number."""
    with pytest.raises(ValidationError):
        SearchRequest(
            query="test",
            page=0  # Invalid page number
        )


def test_search_response_model():
    """Test SearchResponse model."""
    product = Product(
        id="test-1",
        name="Test Product",
        description="A test product",
        category=ProductCategory.ELECTRONICS,
        price=99.99
    )
    
    search_resp = SearchResponse(
        query="test",
        products=[product],
        total=1,
        page=1,
        page_size=20,
        total_pages=1
    )
    
    assert search_resp.query == "test"
    assert len(search_resp.products) == 1
    assert search_resp.total == 1
    assert search_resp.total_pages == 1


def test_chat_message_model():
    """Test ChatMessage model."""
    chat_msg = ChatMessage(
        message="I need a laptop",
        context={"budget": 1000}
    )
    
    assert chat_msg.message == "I need a laptop"
    assert chat_msg.context["budget"] == 1000


def test_chat_response_model():
    """Test ChatResponse model."""
    product = Product(
        id="test-1",
        name="Test Laptop",
        description="A test laptop",
        category=ProductCategory.ELECTRONICS,
        price=999.99
    )
    
    chat_resp = ChatResponse(
        response="I found some great laptops for you!",
        products=[product],
        suggestions=["Show me more", "Compare prices"]
    )
    
    assert "laptops" in chat_resp.response
    assert len(chat_resp.products) == 1
    assert len(chat_resp.suggestions) == 2


def test_health_status_model():
    """Test HealthStatus model."""
    health = HealthStatus(
        status="healthy",
        service="smartshopper-ai",
        version="1.0.0",
        environment="test",
        dependencies={"elasticsearch": "healthy", "redis": "healthy"}
    )
    
    assert health.status == "healthy"
    assert health.service == "smartshopper-ai"
    assert health.dependencies["elasticsearch"] == "healthy"
    assert isinstance(health.timestamp, datetime)


def test_product_category_enum():
    """Test ProductCategory enum values."""
    assert ProductCategory.ELECTRONICS == "electronics"
    assert ProductCategory.CLOTHING == "clothing"
    assert ProductCategory.HOME == "home"
    assert ProductCategory.BOOKS == "books"
    
    # Test enum validation
    product = Product(
        id="test-1",
        name="Test Book",
        description="A test book",
        category="books",  # String should be converted to enum
        price=19.99
    )
    assert product.category == ProductCategory.BOOKS


def test_product_json_serialization():
    """Test Product model JSON serialization."""
    product = Product(
        id="test-1",
        name="Test Product",
        description="A test product",
        category=ProductCategory.ELECTRONICS,
        price=99.99,
        features=["feature1", "feature2"],
        tags=["tag1", "tag2"]
    )
    
    product_dict = product.model_dump()
    
    assert product_dict["id"] == "test-1"
    assert product_dict["category"] == "electronics"
    assert len(product_dict["features"]) == 2
    assert "created_at" in product_dict
    assert "updated_at" in product_dict
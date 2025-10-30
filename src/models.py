"""Data models for SmartShopper AI."""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ProductCategory(str, Enum):
    """Product categories."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME = "home"
    BOOKS = "books"
    SPORTS = "sports"
    BEAUTY = "beauty"
    AUTOMOTIVE = "automotive"
    GROCERIES = "groceries"
    OTHER = "other"


class Product(BaseModel):
    """Product model."""
    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    category: ProductCategory = Field(..., description="Product category")
    price: float = Field(..., ge=0, description="Product price")
    currency: str = Field(default="USD", description="Currency code")
    brand: Optional[str] = Field(None, description="Product brand")
    model: Optional[str] = Field(None, description="Product model")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    
    # Product details
    features: List[str] = Field(default_factory=list, description="Product features")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Technical specifications")
    tags: List[str] = Field(default_factory=list, description="Search tags")
    
    # Availability and ratings
    in_stock: bool = Field(default=True, description="Stock availability")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available quantity")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    
    # URLs and media
    product_url: Optional[HttpUrl] = Field(None, description="Product page URL")
    image_urls: List[HttpUrl] = Field(default_factory=list, description="Product image URLs")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    category: Optional[ProductCategory] = Field(None, description="Filter by category")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    brand: Optional[str] = Field(None, description="Filter by brand")
    in_stock_only: bool = Field(default=True, description="Show only in-stock items")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class SearchResponse(BaseModel):
    """Search response model."""
    query: str = Field(..., description="Original search query")
    products: List[Product] = Field(..., description="Found products")
    total: int = Field(..., ge=0, description="Total number of results")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    products: List[Product] = Field(default_factory=list, description="Recommended products")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up suggestions")
    context: Optional[Dict[str, Any]] = Field(None, description="Conversation context")


class HealthStatus(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment name")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency statuses")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
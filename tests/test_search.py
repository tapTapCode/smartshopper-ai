"""Unit tests for SearchService."""

import pytest
from src.search import SearchService
from src.models import SearchRequest, ProductCategory


@pytest.fixture
def search_service():
    """Create SearchService instance for testing."""
    return SearchService()


class TestBuildSearchQuery:
    """Tests for SearchService._build_search_query method."""
    
    def test_query_only(self, search_service):
        """Test query with only search text."""
        search_request = SearchRequest(query="laptop")
        result = search_service._build_search_query(search_request)
        
        assert "bool" in result
        assert "must" in result["bool"]
        assert len(result["bool"]["must"]) == 1
        assert "multi_match" in result["bool"]["must"][0]
        assert result["bool"]["must"][0]["multi_match"]["query"] == "laptop"
        assert "name^3" in result["bool"]["must"][0]["multi_match"]["fields"]
        assert "description^2" in result["bool"]["must"][0]["multi_match"]["fields"]
        assert "brand^2" in result["bool"]["must"][0]["multi_match"]["fields"]
    
    def test_empty_query(self, search_service):
        """Test query with empty search text uses match_all."""
        search_request = SearchRequest(query="")
        result = search_service._build_search_query(search_request)
        
        assert "bool" in result
        assert "must" in result["bool"]
        assert result["bool"]["must"][0] == {"match_all": {}}
    
    def test_query_with_whitespace(self, search_service):
        """Test query with only whitespace uses match_all."""
        search_request = SearchRequest(query="   ")
        result = search_service._build_search_query(search_request)
        
        assert result["bool"]["must"][0] == {"match_all": {}}
    
    def test_query_with_category(self, search_service):
        """Test query with category filter."""
        search_request = SearchRequest(
            query="smartphone",
            category=ProductCategory.ELECTRONICS
        )
        result = search_service._build_search_query(search_request)
        
        assert "bool" in result
        assert "filter" in result["bool"]
        category_filter = next((f for f in result["bool"]["filter"] if "term" in f and "category" in f["term"]), None)
        assert category_filter is not None
        assert category_filter["term"]["category"] == "electronics"
    
    def test_query_with_brand(self, search_service):
        """Test query with brand filter."""
        search_request = SearchRequest(
            query="laptop",
            brand="Apple"
        )
        result = search_service._build_search_query(search_request)
        
        assert "filter" in result["bool"]
        brand_filter = next((f for f in result["bool"]["filter"] if "term" in f and "brand.keyword" in f["term"]), None)
        assert brand_filter is not None
        assert brand_filter["term"]["brand.keyword"] == "Apple"
    
    def test_query_with_min_price(self, search_service):
        """Test query with minimum price filter."""
        search_request = SearchRequest(
            query="phone",
            min_price=500.0
        )
        result = search_service._build_search_query(search_request)
        
        assert "filter" in result["bool"]
        price_filter = next((f for f in result["bool"]["filter"] if "range" in f and "price" in f["range"]), None)
        assert price_filter is not None
        assert price_filter["range"]["price"]["gte"] == 500.0
        assert "lte" not in price_filter["range"]["price"]
    
    def test_query_with_max_price(self, search_service):
        """Test query with maximum price filter."""
        search_request = SearchRequest(
            query="phone",
            max_price=1000.0
        )
        result = search_service._build_search_query(search_request)
        
        assert "filter" in result["bool"]
        price_filter = next((f for f in result["bool"]["filter"] if "range" in f and "price" in f["range"]), None)
        assert price_filter is not None
        assert price_filter["range"]["price"]["lte"] == 1000.0
        assert "gte" not in price_filter["range"]["price"]
    
    def test_query_with_price_range(self, search_service):
        """Test query with both min and max price filters."""
        search_request = SearchRequest(
            query="laptop",
            min_price=500.0,
            max_price=2000.0
        )
        result = search_service._build_search_query(search_request)
        
        assert "filter" in result["bool"]
        price_filter = next((f for f in result["bool"]["filter"] if "range" in f and "price" in f["range"]), None)
        assert price_filter is not None
        assert price_filter["range"]["price"]["gte"] == 500.0
        assert price_filter["range"]["price"]["lte"] == 2000.0
    
    def test_query_with_in_stock_only(self, search_service):
        """Test query with in_stock_only filter."""
        search_request = SearchRequest(
            query="headphones",
            in_stock_only=True
        )
        result = search_service._build_search_query(search_request)
        
        assert "filter" in result["bool"]
        stock_filter = next((f for f in result["bool"]["filter"] if "term" in f and "in_stock" in f["term"]), None)
        assert stock_filter is not None
        assert stock_filter["term"]["in_stock"] is True
    
    def test_query_without_in_stock_only(self, search_service):
        """Test query without in_stock_only filter."""
        search_request = SearchRequest(
            query="headphones",
            in_stock_only=False
        )
        result = search_service._build_search_query(search_request)
        
        # Should not have in_stock filter when False
        if "filter" in result["bool"]:
            stock_filter = next((f for f in result["bool"]["filter"] if "term" in f and "in_stock" in f["term"]), None)
            assert stock_filter is None
    
    def test_query_with_min_rating(self, search_service):
        """Test query with minimum rating filter."""
        search_request = SearchRequest(
            query="product",
            min_rating=4.0
        )
        result = search_service._build_search_query(search_request)
        
        assert "filter" in result["bool"]
        rating_filter = next((f for f in result["bool"]["filter"] if "range" in f and "rating" in f["range"]), None)
        assert rating_filter is not None
        assert rating_filter["range"]["rating"]["gte"] == 4.0
    
    def test_query_with_all_filters(self, search_service):
        """Test query with all filters combined."""
        search_request = SearchRequest(
            query="smartphone",
            category=ProductCategory.ELECTRONICS,
            min_price=300.0,
            max_price=1500.0,
            brand="Samsung",
            in_stock_only=True,
            min_rating=4.5
        )
        result = search_service._build_search_query(search_request)
        
        assert "bool" in result
        assert "must" in result["bool"]
        assert "filter" in result["bool"]
        
        # Verify multi_match query
        assert result["bool"]["must"][0]["multi_match"]["query"] == "smartphone"
        
        # Verify all filters are present
        filters = result["bool"]["filter"]
        assert len(filters) == 5  # category, price, brand, in_stock, rating
        
        # Check each filter type
        assert any("category" in str(f) for f in filters)
        assert any("brand.keyword" in str(f) for f in filters)
        assert any("in_stock" in str(f) for f in filters)
        
        # Check price range filter
        price_filter = next((f for f in filters if "range" in f and "price" in f["range"]), None)
        assert price_filter is not None
        assert price_filter["range"]["price"]["gte"] == 300.0
        assert price_filter["range"]["price"]["lte"] == 1500.0
        
        # Check rating filter
        rating_filter = next((f for f in filters if "range" in f and "rating" in f["range"]), None)
        assert rating_filter is not None
        assert rating_filter["range"]["rating"]["gte"] == 4.5
    
    def test_query_no_filters(self, search_service):
        """Test query with no filters returns simple bool query."""
        search_request = SearchRequest(
            query="test",
            in_stock_only=False
        )
        result = search_service._build_search_query(search_request)
        
        assert "bool" in result
        assert "must" in result["bool"]
        # Should not have filter clause when no filters applied
        if "filter" in result["bool"]:
            assert len(result["bool"]["filter"]) == 0
    
    def test_query_multiple_categories(self, search_service):
        """Test query structure allows for category filtering."""
        search_request = SearchRequest(
            query="product",
            category=ProductCategory.CLOTHING
        )
        result = search_service._build_search_query(search_request)
        
        category_filter = next((f for f in result["bool"]["filter"] if "term" in f and "category" in f["term"]), None)
        assert category_filter is not None
        assert category_filter["term"]["category"] == "clothing"
    
    def test_query_with_zero_min_price(self, search_service):
        """Test query with zero minimum price is included."""
        search_request = SearchRequest(
            query="product",
            min_price=0.0
        )
        result = search_service._build_search_query(search_request)
        
        assert "filter" in result["bool"]
        price_filter = next((f for f in result["bool"]["filter"] if "range" in f and "price" in f["range"]), None)
        assert price_filter is not None
        assert price_filter["range"]["price"]["gte"] == 0.0
    
    def test_query_with_none_prices(self, search_service):
        """Test query with None price values has no price filter."""
        search_request = SearchRequest(
            query="product",
            min_price=None,
            max_price=None
        )
        result = search_service._build_search_query(search_request)
        
        # Should not have price filter
        if "filter" in result["bool"]:
            price_filter = next((f for f in result["bool"]["filter"] if "range" in f and "price" in f["range"]), None)
            assert price_filter is None
    
    def test_query_special_characters(self, search_service):
        """Test query with special characters in search text."""
        search_request = SearchRequest(query="C++ programming & design")
        result = search_service._build_search_query(search_request)
        
        assert result["bool"]["must"][0]["multi_match"]["query"] == "C++ programming & design"
    
    def test_query_field_boosting(self, search_service):
        """Test that query applies proper field boosting."""
        search_request = SearchRequest(query="test product")
        result = search_service._build_search_query(search_request)
        
        fields = result["bool"]["must"][0]["multi_match"]["fields"]
        # Verify boosting values
        assert "name^3" in fields  # Name has highest boost
        assert "description^2" in fields
        assert "brand^2" in fields
        assert "features" in fields
        assert "tags" in fields
    
    def test_query_category_enum_conversion(self, search_service):
        """Test that ProductCategory enum is properly converted."""
        for category in ProductCategory:
            search_request = SearchRequest(
                query="test",
                category=category
            )
            result = search_service._build_search_query(search_request)
            
            category_filter = next((f for f in result["bool"]["filter"] if "term" in f and "category" in f["term"]), None)
            assert category_filter is not None
            assert category_filter["term"]["category"] == category.value
    
    def test_query_filters_combine_correctly(self, search_service):
        """Test that multiple filters are properly combined."""
        search_request = SearchRequest(
            query="laptop",
            category=ProductCategory.ELECTRONICS,
            brand="Apple",
            min_price=1000.0
        )
        result = search_service._build_search_query(search_request)
        
        # All filters should be in the filter array
        filters = result["bool"]["filter"]
        assert len(filters) == 4  # category, brand, price, in_stock (default True)
        
        # Verify structure
        assert any(f.get("term", {}).get("category") == "electronics" for f in filters)
        assert any(f.get("term", {}).get("brand.keyword") == "Apple" for f in filters)
        assert any(f.get("range", {}).get("price", {}).get("gte") == 1000.0 for f in filters)

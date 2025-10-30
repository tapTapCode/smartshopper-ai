"""Unit tests for CacheService."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.cache import CacheService
from src.models import SearchRequest, ProductCategory


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = Mock()
    client.ping.return_value = True
    client.get.return_value = None
    client.setex.return_value = True
    client.delete.return_value = 1
    client.keys.return_value = []
    client.flushdb.return_value = True
    return client


@pytest.fixture
def cache_service_with_redis(mock_redis_client):
    """Create CacheService with mocked Redis."""
    with patch('src.cache.redis.from_url', return_value=mock_redis_client):
        service = CacheService()
        service.redis_available = True
        service.client = mock_redis_client
        return service


@pytest.fixture
def cache_service_without_redis():
    """Create CacheService without Redis available."""
    with patch('src.cache.HAS_REDIS', False):
        service = CacheService()
        service.redis_available = False
        service.client = None
        return service


class TestCacheBasicOperations:
    """Tests for basic cache operations (get, set, delete)."""
    
    @pytest.mark.asyncio
    async def test_get_existing_value(self, cache_service_with_redis, mock_redis_client):
        """Test getting an existing value from cache."""
        test_data = {"key": "value", "number": 42}
        mock_redis_client.get.return_value = json.dumps(test_data)
        
        result = await cache_service_with_redis.get("test_key")
        
        assert result == test_data
        mock_redis_client.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_value(self, cache_service_with_redis, mock_redis_client):
        """Test getting a non-existent value returns None."""
        mock_redis_client.get.return_value = None
        
        result = await cache_service_with_redis.get("nonexistent_key")
        
        assert result is None
        mock_redis_client.get.assert_called_once_with("nonexistent_key")
    
    @pytest.mark.asyncio
    async def test_set_value_with_default_ttl(self, cache_service_with_redis, mock_redis_client):
        """Test setting a value with default TTL."""
        test_data = {"test": "data"}
        mock_redis_client.setex.return_value = True
        
        result = await cache_service_with_redis.set("test_key", test_data)
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "test_key"
        assert json.loads(call_args[0][2]) == test_data
    
    @pytest.mark.asyncio
    async def test_set_value_with_custom_ttl(self, cache_service_with_redis, mock_redis_client):
        """Test setting a value with custom TTL."""
        test_data = {"test": "data"}
        custom_ttl = 600
        mock_redis_client.setex.return_value = True
        
        result = await cache_service_with_redis.set("test_key", test_data, ttl=custom_ttl)
        
        assert result is True
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][1] == custom_ttl
    
    @pytest.mark.asyncio
    async def test_delete_existing_key(self, cache_service_with_redis, mock_redis_client):
        """Test deleting an existing key."""
        mock_redis_client.delete.return_value = 1
        
        result = await cache_service_with_redis.delete("test_key")
        
        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache_service_with_redis, mock_redis_client):
        """Test deleting a non-existent key returns False."""
        mock_redis_client.delete.return_value = 0
        
        result = await cache_service_with_redis.delete("nonexistent_key")
        
        assert result is False
        mock_redis_client.delete.assert_called_once_with("nonexistent_key")
    
    @pytest.mark.asyncio
    async def test_set_complex_data(self, cache_service_with_redis, mock_redis_client):
        """Test setting complex data structures."""
        complex_data = {
            "list": [1, 2, 3],
            "nested": {"a": 1, "b": 2},
            "string": "test"
        }
        mock_redis_client.setex.return_value = True
        
        result = await cache_service_with_redis.set("complex_key", complex_data)
        
        assert result is True
        call_args = mock_redis_client.setex.call_args
        assert json.loads(call_args[0][2]) == complex_data


class TestCacheGracefulDegradation:
    """Tests for graceful degradation when Redis is unavailable."""
    
    @pytest.mark.asyncio
    async def test_get_when_redis_unavailable(self, cache_service_without_redis):
        """Test get returns None when Redis is unavailable."""
        result = await cache_service_without_redis.get("test_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_when_redis_unavailable(self, cache_service_without_redis):
        """Test set returns False when Redis is unavailable."""
        result = await cache_service_without_redis.set("test_key", {"data": "test"})
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_when_redis_unavailable(self, cache_service_without_redis):
        """Test delete returns False when Redis is unavailable."""
        result = await cache_service_without_redis.delete("test_key")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_when_redis_unavailable(self, cache_service_without_redis):
        """Test health check returns False when Redis is unavailable."""
        result = await cache_service_without_redis.health_check()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_with_redis_error(self, cache_service_with_redis, mock_redis_client):
        """Test get handles Redis errors gracefully."""
        mock_redis_client.get.side_effect = Exception("Redis connection error")
        
        result = await cache_service_with_redis.get("test_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_with_redis_error(self, cache_service_with_redis, mock_redis_client):
        """Test set handles Redis errors gracefully."""
        mock_redis_client.setex.side_effect = Exception("Redis connection error")
        
        result = await cache_service_with_redis.set("test_key", {"data": "test"})
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_with_redis_error(self, cache_service_with_redis, mock_redis_client):
        """Test delete handles Redis errors gracefully."""
        mock_redis_client.delete.side_effect = Exception("Redis connection error")
        
        result = await cache_service_with_redis.delete("test_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_with_redis_error(self, cache_service_with_redis, mock_redis_client):
        """Test health check handles Redis errors gracefully."""
        mock_redis_client.ping.side_effect = Exception("Redis connection error")
        
        result = await cache_service_with_redis.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_with_json_decode_error(self, cache_service_with_redis, mock_redis_client):
        """Test get handles JSON decode errors gracefully."""
        mock_redis_client.get.return_value = "invalid json {{"
        
        result = await cache_service_with_redis.get("test_key")
        
        assert result is None


class TestCacheHelperMethods:
    """Tests for cache helper methods."""
    
    @pytest.mark.asyncio
    async def test_cache_search_results(self, cache_service_with_redis, mock_redis_client):
        """Test caching search results."""
        search_request = SearchRequest(query="laptop", page=1, page_size=10)
        search_response = Mock()
        search_response.model_dump.return_value = {
            "query": "laptop",
            "products": [],
            "total": 0
        }
        
        result = await cache_service_with_redis.cache_search_results(
            search_request, search_response, ttl=300
        )
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_search_results(self, cache_service_with_redis, mock_redis_client):
        """Test getting cached search results."""
        search_request = SearchRequest(query="laptop", page=1, page_size=10)
        cached_data = {"query": "laptop", "products": [], "total": 0}
        mock_redis_client.get.return_value = json.dumps(cached_data)
        
        result = await cache_service_with_redis.get_search_results(search_request)
        
        assert result == cached_data
    
    @pytest.mark.asyncio
    async def test_cache_product(self, cache_service_with_redis, mock_redis_client):
        """Test caching product data."""
        product_data = {"id": "123", "name": "Test Product"}
        
        result = await cache_service_with_redis.cache_product("123", product_data, ttl=3600)
        
        assert result is True
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "product:123"
        assert call_args[0][1] == 3600
    
    @pytest.mark.asyncio
    async def test_get_product(self, cache_service_with_redis, mock_redis_client):
        """Test getting cached product data."""
        product_data = {"id": "123", "name": "Test Product"}
        mock_redis_client.get.return_value = json.dumps(product_data)
        
        result = await cache_service_with_redis.get_product("123")
        
        assert result == product_data
        mock_redis_client.get.assert_called_once_with("product:123")
    
    @pytest.mark.asyncio
    async def test_cache_chat_context(self, cache_service_with_redis, mock_redis_client):
        """Test caching chat context."""
        context = {"last_query": "laptop", "products_shown": 5}
        
        result = await cache_service_with_redis.cache_chat_context("session123", context, ttl=1800)
        
        assert result is True
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "chat_context:session123"
    
    @pytest.mark.asyncio
    async def test_get_chat_context(self, cache_service_with_redis, mock_redis_client):
        """Test getting cached chat context."""
        context = {"last_query": "laptop", "products_shown": 5}
        mock_redis_client.get.return_value = json.dumps(context)
        
        result = await cache_service_with_redis.get_chat_context("session123")
        
        assert result == context
        mock_redis_client.get.assert_called_once_with("chat_context:session123")
    
    @pytest.mark.asyncio
    async def test_clear_cache_with_pattern(self, cache_service_with_redis, mock_redis_client):
        """Test clearing cache with pattern."""
        mock_redis_client.keys.return_value = ["key1", "key2", "key3"]
        mock_redis_client.delete.return_value = 3
        
        result = await cache_service_with_redis.clear_cache("test_*")
        
        assert result == 3
        mock_redis_client.keys.assert_called_once_with("test_*")
        mock_redis_client.delete.assert_called_once_with("key1", "key2", "key3")
    
    @pytest.mark.asyncio
    async def test_clear_cache_all(self, cache_service_with_redis, mock_redis_client):
        """Test clearing all cache."""
        mock_redis_client.flushdb.return_value = True
        
        result = await cache_service_with_redis.clear_cache()
        
        assert result is True
        mock_redis_client.flushdb.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_cache_when_unavailable(self, cache_service_without_redis):
        """Test clearing cache when Redis is unavailable."""
        result = await cache_service_without_redis.clear_cache()
        assert result == 0
    
    def test_generate_cache_key(self, cache_service_with_redis):
        """Test cache key generation is consistent."""
        data1 = {"query": "laptop", "page": 1}
        data2 = {"query": "laptop", "page": 1}
        data3 = {"query": "phone", "page": 1}
        
        key1 = cache_service_with_redis._generate_cache_key("search", data1)
        key2 = cache_service_with_redis._generate_cache_key("search", data2)
        key3 = cache_service_with_redis._generate_cache_key("search", data3)
        
        # Same data should produce same key
        assert key1 == key2
        # Different data should produce different key
        assert key1 != key3
        # Key should have prefix
        assert key1.startswith("search:")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, cache_service_with_redis, mock_redis_client):
        """Test health check returns True when Redis is healthy."""
        mock_redis_client.ping.return_value = True
        
        result = await cache_service_with_redis.health_check()
        
        assert result is True
        mock_redis_client.ping.assert_called_once()


class TestCacheInitialization:
    """Tests for CacheService initialization."""
    
    def test_init_with_redis_available(self, mock_redis_client):
        """Test initialization when Redis is available."""
        with patch('src.cache.redis.from_url', return_value=mock_redis_client):
            service = CacheService()
            
            assert service.redis_available is True
            assert service.client is not None
    
    def test_init_without_redis_library(self):
        """Test initialization when redis library is not installed."""
        with patch('src.cache.HAS_REDIS', False):
            service = CacheService()
            
            assert service.redis_available is False
            assert service.client is None
    
    def test_init_with_redis_connection_error(self, mock_redis_client):
        """Test initialization when Redis connection fails."""
        mock_redis_client.ping.side_effect = Exception("Connection refused")
        
        with patch('src.cache.redis.from_url', return_value=mock_redis_client):
            service = CacheService()
            
            assert service.redis_available is False

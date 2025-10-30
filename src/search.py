"""Elasticsearch integration for product search."""

from elasticsearch import Elasticsearch
from typing import List, Optional, Dict, Any
import logging

from .config import settings
from .models import Product, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)


class SearchService:
    """Elasticsearch-based product search service."""
    
    def __init__(self):
        """Initialize Elasticsearch client."""
        self.es = Elasticsearch([settings.elasticsearch_url])
        self.index_name = settings.products_index_name
        
    async def ensure_index_exists(self) -> bool:
        """Ensure the products index exists with proper mapping."""
        try:
            if not self.es.indices.exists(index=self.index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "id": {"type": "keyword"},
                            "name": {
                                "type": "text",
                                "analyzer": "standard",
                                "fields": {"keyword": {"type": "keyword"}}
                            },
                            "description": {
                                "type": "text",
                                "analyzer": "standard"
                            },
                            "category": {"type": "keyword"},
                            "price": {"type": "float"},
                            "currency": {"type": "keyword"},
                            "brand": {
                                "type": "text",
                                "fields": {"keyword": {"type": "keyword"}}
                            },
                            "model": {"type": "keyword"},
                            "sku": {"type": "keyword"},
                            "features": {"type": "text"},
                            "specifications": {"type": "object"},
                            "tags": {"type": "keyword"},
                            "in_stock": {"type": "boolean"},
                            "stock_quantity": {"type": "integer"},
                            "rating": {"type": "float"},
                            "review_count": {"type": "integer"},
                            "product_url": {"type": "keyword"},
                            "image_urls": {"type": "keyword"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
                
                self.es.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
            return False
    
    async def index_product(self, product: Product) -> bool:
        """Index a single product."""
        try:
            doc = product.model_dump()
            # Convert datetime objects to strings
            doc["created_at"] = doc["created_at"].isoformat() if hasattr(doc["created_at"], "isoformat") else doc["created_at"]
            doc["updated_at"] = doc["updated_at"].isoformat() if hasattr(doc["updated_at"], "isoformat") else doc["updated_at"]
            
            result = self.es.index(
                index=self.index_name,
                id=product.id,
                body=doc
            )
            return result["result"] in ["created", "updated"]
        except Exception as e:
            logger.error(f"Error indexing product {product.id}: {e}")
            return False
    
    async def index_products(self, products: List[Product]) -> int:
        """Bulk index multiple products."""
        if not products:
            return 0
            
        try:
            from elasticsearch.helpers import bulk
            
            actions = []
            for product in products:
                doc = product.model_dump()
                # Convert datetime objects to strings
                doc["created_at"] = doc["created_at"].isoformat() if hasattr(doc["created_at"], "isoformat") else doc["created_at"]
                doc["updated_at"] = doc["updated_at"].isoformat() if hasattr(doc["updated_at"], "isoformat") else doc["updated_at"]
                
                actions.append({
                    "_index": self.index_name,
                    "_id": product.id,
                    "_source": doc
                })
            
            success_count, errors = bulk(self.es, actions)
            if errors:
                logger.warning(f"Bulk indexing had errors: {errors}")
            
            # Refresh index to make documents searchable immediately
            self.es.indices.refresh(index=self.index_name)
            
            return success_count
        except Exception as e:
            logger.error(f"Error bulk indexing products: {e}")
            return 0
    
    async def search_products(self, search_request: SearchRequest) -> SearchResponse:
        """Search for products based on the request."""
        try:
            # Build the query
            query = self._build_search_query(search_request)
            
            # Calculate pagination
            from_index = (search_request.page - 1) * search_request.page_size
            
            # Execute search
            response = self.es.search(
                index=self.index_name,
                body={
                    "query": query,
                    "from": from_index,
                    "size": search_request.page_size,
                    "sort": [{"_score": {"order": "desc"}}]
                }
            )
            
            # Parse results
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            
            products = []
            for hit in hits:
                try:
                    product_data = hit["_source"]
                    product = Product(**product_data)
                    products.append(product)
                except Exception as e:
                    logger.warning(f"Error parsing product from search result: {e}")
            
            total_pages = (total + search_request.page_size - 1) // search_request.page_size
            
            return SearchResponse(
                query=search_request.query,
                products=products,
                total=total,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return SearchResponse(
                query=search_request.query,
                products=[],
                total=0,
                page=search_request.page,
                page_size=search_request.page_size,
                total_pages=0
            )
    
    def _build_search_query(self, search_request: SearchRequest) -> Dict[str, Any]:
        """Build Elasticsearch query from search request."""
        must_clauses = []
        filter_clauses = []
        
        # Text search
        if search_request.query.strip():
            must_clauses.append({
                "multi_match": {
                    "query": search_request.query,
                    "fields": ["name^3", "description^2", "brand^2", "features", "tags"]
                }
            })
        else:
            must_clauses.append({"match_all": {}})
        
        # Filters
        if search_request.category:
            filter_clauses.append({"term": {"category": search_request.category}})
        
        if search_request.brand:
            filter_clauses.append({"term": {"brand.keyword": search_request.brand}})
        
        if search_request.in_stock_only:
            filter_clauses.append({"term": {"in_stock": True}})
        
        # Price range
        price_range = {}
        if search_request.min_price is not None:
            price_range["gte"] = search_request.min_price
        if search_request.max_price is not None:
            price_range["lte"] = search_request.max_price
        if price_range:
            filter_clauses.append({"range": {"price": price_range}})
        
        # Rating filter
        if search_request.min_rating is not None:
            filter_clauses.append({"range": {"rating": {"gte": search_request.min_rating}}})
        
        # Construct final query
        if filter_clauses:
            return {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            }
        else:
            return {"bool": {"must": must_clauses}}
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single product by ID."""
        try:
            response = self.es.get(index=self.index_name, id=product_id)
            return Product(**response["_source"])
        except Exception as e:
            logger.warning(f"Product {product_id} not found: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if Elasticsearch is healthy."""
        try:
            health = self.es.cluster.health()
            return health["status"] in ["green", "yellow"]
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return False


# Global search service instance
search_service = SearchService()
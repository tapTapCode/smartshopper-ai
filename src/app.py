"""Main Flask application for SmartShopper AI."""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
from typing import Dict, Any
import asyncio
import os

from .config import settings
from .models import SearchRequest, ChatMessage, HealthStatus, VisualSearchRequest, VisualSearchResponse
from .search import search_service
from .ai_service import ai_service
from .vision_service import vision_service


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.flask_debug
    
    # Enable CORS for frontend integration
    CORS(app)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    @app.route("/")
    def home():
        """Serve the main interface."""
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        return send_from_directory(static_dir, 'index.html')
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files."""
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        return send_from_directory(static_dir, filename)
    
    @app.route("/api")
    def api_info() -> Dict[str, str]:
        """API info endpoint."""
        return {"message": "Welcome to SmartShopper AI API", "version": "1.0.0"}
    
    @app.route("/health")
    def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        # Check dependencies
        dependencies = {}
        
        # Check Elasticsearch
        try:
            es_healthy = asyncio.run(search_service.health_check())
            dependencies["elasticsearch"] = "healthy" if es_healthy else "unhealthy"
        except Exception:
            dependencies["elasticsearch"] = "unhealthy"
        
        # Check AI services
        dependencies["vertex_ai"] = "available" if ai_service.vertex_ai_available else "unavailable"
        dependencies["openai"] = "available" if ai_service.openai_available else "unavailable"
        
        # Check Vision services
        dependencies["clip_model"] = "available" if vision_service.clip_model else "unavailable"
        dependencies["gemini_vision"] = "available" if vision_service.gemini_vision_available else "unavailable"
        
        health_status = HealthStatus(
            status="healthy",
            service="smartshopper-ai",
            version="1.0.0",
            environment=settings.flask_env,
            dependencies=dependencies
        )
        
        return health_status.model_dump()
    
    @app.route("/api/search", methods=["POST"])
    def search_products() -> Dict[str, Any]:
        """Search products endpoint."""
        try:
            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400
            
            # Create search request from JSON data
            search_request = SearchRequest(**data)
            
            # Perform search
            search_response = asyncio.run(search_service.search_products(search_request))
            
            return search_response.model_dump()
            
        except ValueError as e:
            return {"error": f"Invalid request data: {str(e)}"}, 400
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"error": "Internal server error"}, 500
    
    @app.route("/api/chat", methods=["POST"])
    def chat() -> Dict[str, Any]:
        """Conversational chat endpoint."""
        try:
            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400
            
            # Create chat message from JSON data
            chat_message = ChatMessage(**data)
            
            # Process chat message
            chat_response = asyncio.run(ai_service.chat(chat_message))
            
            return chat_response.model_dump()
            
        except ValueError as e:
            return {"error": f"Invalid request data: {str(e)}"}, 400
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {"error": "Internal server error"}, 500
    
    @app.route("/api/visual-search", methods=["POST"])
    def visual_search() -> Dict[str, Any]:
        """Visual product search endpoint using image upload."""
        import time
        
        try:
            start_time = time.time()
            
            # Check if image is provided
            if 'image' not in request.files:
                return {"error": "No image file provided"}, 400
            
            image_file = request.files['image']
            
            if image_file.filename == '':
                return {"error": "Empty filename"}, 400
            
            # Read image bytes
            image_bytes = image_file.read()
            
            # Get optional parameters from form data
            params = {
                "min_price": request.form.get('min_price', type=float),
                "max_price": request.form.get('max_price', type=float),
                "category": request.form.get('category'),
                "top_k": request.form.get('top_k', default=10, type=int),
                "use_gemini_analysis": request.form.get('use_gemini_analysis', default='true').lower() == 'true'
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Create visual search request
            search_request = VisualSearchRequest(**params)
            
            # Generate image embedding
            query_embedding = asyncio.run(vision_service.generate_image_embedding(image_bytes))
            
            if query_embedding is None:
                return {"error": "Failed to generate image embedding. Make sure CLIP model is loaded."}, 500
            
            # Optional: Analyze image with Gemini Vision
            gemini_analysis = None
            if search_request.use_gemini_analysis:
                gemini_analysis = asyncio.run(vision_service.analyze_image_with_gemini(image_bytes))
            
            # Search for similar products
            # For now, we'll search all products and filter by similarity
            # In production, you'd use Elasticsearch vector search
            all_products_search = asyncio.run(search_service.search_products(
                SearchRequest(query="*", page_size=1000)
            ))
            
            # Build product embeddings list
            product_embeddings = []
            for product in all_products_search.products:
                if product.image_embedding:
                    # Convert list back to numpy array
                    import numpy as np
                    embedding = np.array(product.image_embedding)
                    product_embeddings.append((product.id, embedding))
            
            # Find similar products
            similar_products_ids = asyncio.run(vision_service.search_similar_products(
                query_embedding=query_embedding,
                product_embeddings=product_embeddings,
                top_k=search_request.top_k
            ))
            
            # Fetch full product details
            similar_products = []
            for product in all_products_search.products:
                for product_id, similarity in similar_products_ids:
                    if product.id == product_id:
                        similar_products.append(product)
                        break
            
            # Apply filters if specified
            if search_request.category:
                similar_products = [p for p in similar_products if p.category == search_request.category]
            
            if search_request.min_price is not None:
                similar_products = [p for p in similar_products if p.price >= search_request.min_price]
            
            if search_request.max_price is not None:
                similar_products = [p for p in similar_products if p.price <= search_request.max_price]
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Create response
            response = VisualSearchResponse(
                products=similar_products[:search_request.top_k],
                total=len(similar_products),
                gemini_analysis=gemini_analysis,
                search_time_ms=search_time_ms
            )
            
            return response.model_dump()
            
        except ValueError as e:
            return {"error": f"Invalid request data: {str(e)}"}, 400
        except Exception as e:
            logger.error(f"Visual search error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Internal server error: {str(e)}"}, 500
    
    @app.errorhandler(404)
    def not_found(error) -> tuple[Dict[str, str], int]:
        """Handle 404 errors."""
        return {"error": "Endpoint not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error) -> tuple[Dict[str, str], int]:
        """Handle 500 errors."""
        logger.error(f"Internal error: {error}")
        return {"error": "Internal server error"}, 500
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=settings.flask_debug)
"""Main Flask application for SmartShopper AI."""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
from typing import Dict, Any
import asyncio
import os

from .config import settings
from .models import SearchRequest, ChatMessage, HealthStatus
from .search import search_service
from .ai_service import ai_service


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
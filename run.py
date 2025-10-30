#!/usr/bin/env python3
"""
SmartShopper AI Application Runner
Run this script to start the application with sample data.
"""

import os
import sys
import asyncio
import logging

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app
from src.sample_data import index_sample_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def initialize_data():
    """Initialize sample data if needed."""
    try:
        logger.info("Initializing sample data...")
        count = await index_sample_data()
        if count > 0:
            logger.info(f"Successfully indexed {count} sample products")
        else:
            logger.warning("No products were indexed")
    except Exception as e:
        logger.error(f"Failed to initialize sample data: {e}")


def main():
    """Main application entry point."""
    logger.info("Starting SmartShopper AI...")
    
    # Initialize sample data
    try:
        asyncio.run(initialize_data())
    except Exception as e:
        logger.error(f"Data initialization failed: {e}")
        logger.info("Continuing without sample data...")
    
    # Create and run Flask app
    app = create_app()
    
    logger.info("SmartShopper AI started successfully!")
    logger.info("Visit http://localhost:5000 to access the application")
    logger.info("API endpoints available at:")
    logger.info("  - GET  /health      - Health check")
    logger.info("  - POST /api/search  - Product search")
    logger.info("  - POST /api/chat    - Conversational AI")
    
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
"""Configuration settings for SmartShopper AI."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Flask Configuration
    flask_env: str = "development"
    flask_debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Database Configuration
    elasticsearch_url: str = "http://localhost:9200"
    redis_url: str = "redis://localhost:6379/0"
    
    # Google Cloud Configuration
    google_cloud_project: Optional[str] = None
    google_application_credentials: Optional[str] = None
    vertex_ai_location: str = "us-central1"
    
    # OpenAI Configuration (alternative)
    openai_api_key: Optional[str] = None
    
    # Application Configuration
    products_index_name: str = "smartshopper_products"
    cache_ttl: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
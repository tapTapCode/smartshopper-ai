"""AI service for conversational product recommendations."""

import json
import logging
from typing import Optional, List, Dict, Any
import asyncio

try:
    from google.cloud import aiplatform
    from google.cloud.aiplatform import gapic
    HAS_VERTEX_AI = True
except ImportError:
    HAS_VERTEX_AI = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from .config import settings
from .models import ChatMessage, ChatResponse, Product, ProductCategory, SearchRequest
from .search import search_service

logger = logging.getLogger(__name__)


class AIService:
    """Conversational AI service for product recommendations."""
    
    def __init__(self):
        """Initialize AI service with available providers."""
        self.vertex_ai_available = False
        self.openai_available = False
        
        # Initialize Vertex AI if available and configured
        if HAS_VERTEX_AI and settings.google_cloud_project:
            try:
                aiplatform.init(
                    project=settings.google_cloud_project,
                    location=settings.vertex_ai_location
                )
                self.vertex_ai_available = True
                logger.info("Vertex AI initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {e}")
        
        # Initialize OpenAI if available and configured
        if HAS_OPENAI and settings.openai_api_key:
            try:
                openai.api_key = settings.openai_api_key
                self.openai_available = True
                logger.info("OpenAI initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
    
    async def chat(self, message: ChatMessage) -> ChatResponse:
        """Process a chat message and return AI response with product recommendations."""
        try:
            # Extract potential search intent from the message
            search_terms = self._extract_search_terms(message.message)
            
            # Search for relevant products
            products = []
            if search_terms:
                search_request = SearchRequest(
                    query=search_terms,
                    page_size=5  # Limit to top 5 recommendations
                )
                search_response = await search_service.search_products(search_request)
                products = search_response.products
            
            # Generate AI response
            ai_response = await self._generate_response(message.message, products)
            
            # Generate follow-up suggestions
            suggestions = self._generate_suggestions(message.message, products)
            
            return ChatResponse(
                response=ai_response,
                products=products,
                suggestions=suggestions,
                context={"search_terms": search_terms}
            )
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            return ChatResponse(
                response="I apologize, but I'm having trouble processing your request right now. Please try again later.",
                products=[],
                suggestions=["Try a different search", "Browse categories", "Contact support"],
                context=None
            )
    
    def _extract_search_terms(self, message: str) -> str:
        """Extract search terms from user message using simple keyword matching."""
        # Convert to lowercase for matching
        message_lower = message.lower()
        
        # Common shopping keywords and their mappings
        category_keywords = {
            "phone": "smartphone",
            "laptop": "laptop",
            "headphones": "headphones",
            "jeans": "jeans",
            "cooking": "kitchen",
            "book": "programming",
            "shoes": "sneakers",
            "skincare": "moisturizer"
        }
        
        # Brand keywords
        brand_keywords = [
            "apple", "iphone", "macbook",
            "sony", "nike", "levi's", "levis",
            "instant pot", "cerave"
        ]
        
        # Look for category matches
        for keyword, search_term in category_keywords.items():
            if keyword in message_lower:
                return search_term
        
        # Look for brand matches
        for brand in brand_keywords:
            if brand in message_lower:
                return brand
        
        # Price-related queries
        if any(word in message_lower for word in ["cheap", "budget", "affordable", "under"]):
            return "budget"
        elif any(word in message_lower for word in ["premium", "expensive", "high-end", "best"]):
            return "premium"
        
        # If no specific keywords found, use the entire message as search term
        # but clean it up a bit
        cleaned_message = message.replace("?", "").replace("!", "").strip()
        if len(cleaned_message) > 50:
            # If message is too long, extract key words
            words = cleaned_message.split()
            # Keep nouns and adjectives (simple heuristic)
            key_words = [word for word in words if len(word) > 3 and not word.lower() in 
                        ["what", "where", "when", "how", "can", "could", "would", "should", "the", "and", "or", "but"]]
            return " ".join(key_words[:5])  # Limit to 5 key words
        
        return cleaned_message
    
    async def _generate_response(self, user_message: str, products: List[Product]) -> str:
        """Generate AI response using available AI services."""
        
        # Create context about found products
        product_context = ""
        if products:
            product_context = f"Based on your request, I found {len(products)} relevant products:\\n"
            for i, product in enumerate(products[:3], 1):
                product_context += f"{i}. {product.name} by {product.brand} - ${product.price} (Rating: {product.rating}/5)\\n"
        
        # Try Vertex AI first
        if self.vertex_ai_available:
            try:
                return await self._generate_vertex_ai_response(user_message, product_context)
            except Exception as e:
                logger.warning(f"Vertex AI response generation failed: {e}")
        
        # Fall back to OpenAI
        if self.openai_available:
            try:
                return await self._generate_openai_response(user_message, product_context)
            except Exception as e:
                logger.warning(f"OpenAI response generation failed: {e}")
        
        # Fallback to rule-based response
        return self._generate_fallback_response(user_message, products)
    
    async def _generate_vertex_ai_response(self, user_message: str, product_context: str) -> str:
        """Generate response using Vertex AI."""
        prompt = f"""You are SmartShopper AI, a helpful shopping assistant. Respond naturally and conversationally to help users find products.

User message: {user_message}

{product_context}

Provide a helpful, friendly response. If products were found, briefly highlight the best options and explain why they might be good choices. Keep your response concise (2-3 sentences) and focused on helping the user make a decision."""

        try:
            # Use Vertex AI's text generation
            from google.cloud.aiplatform import gapic
            
            client = gapic.PredictionServiceClient()
            endpoint = f"projects/{settings.google_cloud_project}/locations/{settings.vertex_ai_location}/publishers/google/models/text-bison"
            
            instance = {
                "prompt": prompt,
                "max_output_tokens": 150,
                "temperature": 0.7
            }
            
            response = client.predict(
                endpoint=endpoint,
                instances=[instance]
            )
            
            return response.predictions[0]["content"]
            
        except Exception as e:
            logger.error(f"Vertex AI generation error: {e}")
            raise
    
    async def _generate_openai_response(self, user_message: str, product_context: str) -> str:
        """Generate response using OpenAI."""
        prompt = f"""You are SmartShopper AI, a helpful shopping assistant. Respond naturally and conversationally to help users find products.

User message: {user_message}

{product_context}

Provide a helpful, friendly response. If products were found, briefly highlight the best options and explain why they might be good choices. Keep your response concise (2-3 sentences) and focused on helping the user make a decision."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are SmartShopper AI, a helpful shopping assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    def _generate_fallback_response(self, user_message: str, products: List[Product]) -> str:
        """Generate a simple rule-based response when AI services are unavailable."""
        message_lower = user_message.lower()
        
        if products:
            if len(products) == 1:
                product = products[0]
                return f"I found a great option for you: the {product.name} by {product.brand} for ${product.price}. It has a {product.rating}/5 rating and is currently in stock!"
            else:
                top_product = products[0]
                return f"I found {len(products)} great options! The top recommendation is the {top_product.name} by {top_product.brand} for ${top_product.price}. Would you like to see more details or filter by price range?"
        else:
            if any(word in message_lower for word in ["hello", "hi", "hey"]):
                return "Hello! I'm SmartShopper AI, your personal shopping assistant. I can help you find products, compare prices, and make recommendations. What are you looking for today?"
            elif any(word in message_lower for word in ["help", "what can you do"]):
                return "I can help you find products across categories like electronics, clothing, home goods, books, and more! Just tell me what you're looking for, your budget, or any specific preferences."
            else:
                return "I couldn't find any products matching your request, but I'm here to help! Try describing what you're looking for in different terms, or let me know your budget and preferences."
    
    def _generate_suggestions(self, user_message: str, products: List[Product]) -> List[str]:
        """Generate follow-up suggestions based on the conversation."""
        suggestions = []
        
        if products:
            # Suggest related categories or actions
            categories = set(product.category for product in products)
            if ProductCategory.ELECTRONICS in categories:
                suggestions.extend([
                    "Show me more electronics",
                    "Compare similar products",
                    "Find budget electronics"
                ])
            
            # Suggest price-based filters
            prices = [product.price for product in products]
            if prices:
                avg_price = sum(prices) / len(prices)
                suggestions.append(f"Find products under ${int(avg_price)}")
                suggestions.append(f"Show premium options above ${int(avg_price)}")
        else:
            # General suggestions when no products found
            suggestions.extend([
                "Browse popular products",
                "Show me deals and discounts",
                "Help me find something specific",
                "Show me trending items"
            ])
        
        return suggestions[:3]  # Limit to 3 suggestions


# Global AI service instance
ai_service = AIService()
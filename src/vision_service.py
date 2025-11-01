"""Vision-based product search using CLIP embeddings and Gemini Vision API."""

import logging
import numpy as np
from typing import List, Optional, Tuple
import io
from PIL import Image
import base64

try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    HAS_CLIP = True
except ImportError:
    HAS_CLIP = False

try:
    from google.cloud import aiplatform
    from vertexai.preview.vision_models import ImageTextModel, Image as VertexImage
    import vertexai
    HAS_GEMINI_VISION = True
except ImportError:
    HAS_GEMINI_VISION = False

from .config import settings

logger = logging.getLogger(__name__)


class VisionService:
    """Service for image-based product search and analysis."""
    
    def __init__(self):
        """Initialize vision service with CLIP and Gemini Vision."""
        self.clip_model = None
        self.clip_processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu" if HAS_CLIP else None
        self.gemini_vision_available = False
        
        # Initialize CLIP model
        if HAS_CLIP:
            try:
                logger.info(f"Loading CLIP model on device: {self.device}")
                self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                
                if self.device == "cuda":
                    self.clip_model = self.clip_model.to(self.device)
                
                self.clip_model.eval()
                logger.info("CLIP model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load CLIP model: {e}")
                self.clip_model = None
        
        # Initialize Gemini Vision API
        if HAS_GEMINI_VISION and settings.google_cloud_project:
            try:
                vertexai.init(
                    project=settings.google_cloud_project,
                    location=settings.vertex_ai_location
                )
                self.gemini_vision_available = True
                logger.info("Gemini Vision API initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini Vision: {e}")
    
    async def generate_image_embedding(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Generate embedding vector for an image using CLIP.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Embedding vector as numpy array, or None if generation fails
        """
        if not self.clip_model or not self.clip_processor:
            logger.error("CLIP model not available")
            return None
        
        try:
            # Load and preprocess image
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Process image
            inputs = self.clip_processor(images=image, return_tensors="pt")
            
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                
            # Normalize embedding
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy array
            embedding = image_features.cpu().numpy().flatten()
            
            logger.info(f"Generated image embedding with shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate image embedding: {e}")
            return None
    
    async def generate_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding vector for text using CLIP.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array, or None if generation fails
        """
        if not self.clip_model or not self.clip_processor:
            logger.error("CLIP model not available")
            return None
        
        try:
            # Process text
            inputs = self.clip_processor(text=[text], return_tensors="pt", padding=True)
            
            if self.device == "cuda":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                text_features = self.clip_model.get_text_features(**inputs)
            
            # Normalize embedding
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Convert to numpy array
            embedding = text_features.cpu().numpy().flatten()
            
            logger.info(f"Generated text embedding with shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            return None
    
    async def analyze_image_with_gemini(self, image_bytes: bytes) -> Optional[dict]:
        """
        Analyze product image using Gemini Vision API to extract attributes.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with extracted attributes (category, color, style, etc.)
        """
        if not self.gemini_vision_available:
            logger.warning("Gemini Vision not available")
            return None
        
        try:
            # Prepare image for Gemini
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to base64 for Gemini API
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Use Gemini to analyze the image
            from vertexai.generative_models import GenerativeModel, Part
            
            model = GenerativeModel("gemini-1.5-flash")
            
            prompt = """Analyze this product image and extract the following information in JSON format:
{
  "product_type": "general category of the product",
  "category": "specific category (electronics, clothing, home, books, sports, beauty, automotive, groceries, other)",
  "colors": ["list of prominent colors"],
  "style": "style or design description",
  "brand_visible": "brand name if visible, otherwise null",
  "key_features": ["list of visible features"],
  "condition": "new/used/refurbished if determinable",
  "estimated_price_range": "budget/mid-range/premium"
}

Provide only the JSON response, no additional text."""

            image_part = Part.from_data(data=image_bytes, mime_type="image/png")
            
            response = model.generate_content([prompt, image_part])
            
            # Parse response
            import json
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            logger.info(f"Gemini Vision analysis: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze image with Gemini: {e}")
            return None
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Normalize vectors
            embedding1 = embedding1 / np.linalg.norm(embedding1)
            embedding2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    async def search_similar_products(
        self,
        query_embedding: np.ndarray,
        product_embeddings: List[Tuple[str, np.ndarray]],
        top_k: int = 10,
        threshold: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find products most similar to the query embedding.
        
        Args:
            query_embedding: Query image embedding
            product_embeddings: List of (product_id, embedding) tuples
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (product_id, similarity_score) tuples, sorted by similarity
        """
        try:
            similarities = []
            
            for product_id, product_embedding in product_embeddings:
                similarity = self.calculate_similarity(query_embedding, product_embedding)
                
                if similarity >= threshold:
                    similarities.append((product_id, similarity))
            
            # Sort by similarity (descending) and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search similar products: {e}")
            return []


# Global vision service instance
vision_service = VisionService()

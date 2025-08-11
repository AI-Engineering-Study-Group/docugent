"""
Embedding Service for multimodal document search.
Handles text and image embeddings using various models.
"""

import os
import json
import numpy as np
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import hashlib
from dataclasses import dataclass
import pickle

from app.config.logger import Logger

logger = Logger.get_logger(__name__)

@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    chunk_id: str
    embedding: np.ndarray
    embedding_type: str  # 'text' or 'image'
    model_name: str
    metadata: Dict[str, Any]

class EmbeddingService:
    """Service for generating and managing embeddings."""
    
    def __init__(self):
        self.embeddings_dir = Path("data/uploads/embeddings")
        self.embeddings_dir.mkdir(exist_ok=True)
        
        # Initialize embedding models (placeholder for now)
        self.text_model = None
        self.image_model = None
        
        # For now, we'll use simple TF-IDF like embeddings
        # In production, you'd use models like:
        # - Text: sentence-transformers, OpenAI embeddings
        # - Image: CLIP, DALL-E embeddings
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize embedding models."""
        try:
            # Placeholder for model initialization
            # In a real implementation, you'd load actual models here
            logger.info("Initializing embedding models...")
            
            # Example: Load sentence transformers for text
            # from sentence_transformers import SentenceTransformer
            # self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Example: Load CLIP for images
            # import clip
            # self.image_model, self.preprocess = clip.load("ViT-B/32", device="cpu")
            
            logger.info("Embedding models initialized successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize embedding models: {e}")
            logger.info("Using fallback embedding methods")
    
    def _generate_simple_text_embedding(self, text: str) -> np.ndarray:
        """
        Generate a simple text embedding using TF-IDF like approach.
        This is a fallback when proper embedding models aren't available.
        """
        # Simple character-based embedding (very basic)
        # In production, use proper embedding models
        text_lower = text.lower()
        
        # Create a simple feature vector
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'sentence_count': len([s for s in text.split('.') if s.strip()]),
            'avg_word_length': np.mean([len(word) for word in text.split()]) if text.split() else 0,
            'unique_chars': len(set(text_lower)),
            'digit_count': sum(c.isdigit() for c in text),
            'uppercase_count': sum(c.isupper() for c in text),
            'punctuation_count': sum(c in '.,!?;:' for c in text)
        }
        
        # Convert to numpy array
        embedding = np.array(list(features.values()), dtype=np.float32)
        
        # Normalize
        if np.linalg.norm(embedding) > 0:
            embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def _generate_simple_image_embedding(self, image_path: str) -> np.ndarray:
        """
        Generate a simple image embedding.
        This is a fallback when proper image embedding models aren't available.
        """
        try:
            from PIL import Image
            import io
            
            # Load image
            with open(image_path, 'rb') as f:
                img = Image.open(f)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to standard size
            img = img.resize((224, 224))
            
            # Convert to numpy array
            img_array = np.array(img)
            
            # Create simple features
            features = {
                'mean_r': np.mean(img_array[:, :, 0]),
                'mean_g': np.mean(img_array[:, :, 1]),
                'mean_b': np.mean(img_array[:, :, 2]),
                'std_r': np.std(img_array[:, :, 0]),
                'std_g': np.std(img_array[:, :, 1]),
                'std_b': np.std(img_array[:, :, 2]),
                'brightness': np.mean(img_array),
                'contrast': np.std(img_array),
                'aspect_ratio': img_array.shape[1] / img_array.shape[0],
                'size': img_array.shape[0] * img_array.shape[1]
            }
            
            # Convert to numpy array
            embedding = np.array(list(features.values()), dtype=np.float32)
            
            # Normalize
            if np.linalg.norm(embedding) > 0:
                embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating image embedding: {e}")
            # Return zero embedding as fallback
            return np.zeros(10, dtype=np.float32)
    
    def generate_text_embedding(self, text: str, chunk_id: str) -> EmbeddingResult:
        """
        Generate text embedding for a chunk.
        
        Args:
            text: Text content to embed
            chunk_id: Unique identifier for the chunk
            
        Returns:
            EmbeddingResult with the generated embedding
        """
        try:
            if self.text_model:
                # Use proper embedding model
                embedding = self.text_model.encode(text)
            else:
                # Use fallback method
                embedding = self._generate_simple_text_embedding(text)
            
            result = EmbeddingResult(
                chunk_id=chunk_id,
                embedding=embedding,
                embedding_type='text',
                model_name='simple_text_model',
                metadata={
                    'text_length': len(text),
                    'word_count': len(text.split())
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            raise
    
    def generate_image_embedding(self, image_path: str, chunk_id: str) -> EmbeddingResult:
        """
        Generate image embedding for a chunk.
        
        Args:
            image_path: Path to the image file
            chunk_id: Unique identifier for the chunk
            
        Returns:
            EmbeddingResult with the generated embedding
        """
        try:
            if self.image_model:
                # Use proper image embedding model
                # This would involve preprocessing and model inference
                embedding = np.random.rand(512)  # Placeholder
            else:
                # Use fallback method
                embedding = self._generate_simple_image_embedding(image_path)
            
            result = EmbeddingResult(
                chunk_id=chunk_id,
                embedding=embedding,
                embedding_type='image',
                model_name='simple_image_model',
                metadata={
                    'image_path': image_path,
                    'embedding_dim': len(embedding)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating image embedding: {e}")
            raise
    
    def save_embeddings(self, file_hash: str, embeddings: List[EmbeddingResult]) -> bool:
        """
        Save embeddings for a document.
        
        Args:
            file_hash: Hash of the document
            embeddings: List of embedding results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            embeddings_file = self.embeddings_dir / f"{file_hash}_embeddings.pkl"
            
            # Convert embeddings to serializable format
            embeddings_data = []
            for emb in embeddings:
                emb_data = {
                    'chunk_id': emb.chunk_id,
                    'embedding': emb.embedding,
                    'embedding_type': emb.embedding_type,
                    'model_name': emb.model_name,
                    'metadata': emb.metadata
                }
                embeddings_data.append(emb_data)
            
            # Save using pickle
            with open(embeddings_file, 'wb') as f:
                pickle.dump(embeddings_data, f)
            
            logger.info(f"Saved {len(embeddings)} embeddings for document {file_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            return False
    
    def load_embeddings(self, file_hash: str) -> List[EmbeddingResult]:
        """
        Load embeddings for a document.
        
        Args:
            file_hash: Hash of the document
            
        Returns:
            List of embedding results
        """
        try:
            embeddings_file = self.embeddings_dir / f"{file_hash}_embeddings.pkl"
            
            if not embeddings_file.exists():
                return []
            
            with open(embeddings_file, 'rb') as f:
                embeddings_data = pickle.load(f)
            
            # Convert back to EmbeddingResult objects
            embeddings = []
            for emb_data in embeddings_data:
                emb = EmbeddingResult(
                    chunk_id=emb_data['chunk_id'],
                    embedding=emb_data['embedding'],
                    embedding_type=emb_data['embedding_type'],
                    model_name=emb_data['model_name'],
                    metadata=emb_data['metadata']
                )
                embeddings.append(emb)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return []
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Ensure embeddings are normalized
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def search_similar_chunks(self, query_embedding: np.ndarray, file_hash: str = None, 
                            top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for chunks similar to the query embedding.
        
        Args:
            query_embedding: Query embedding
            file_hash: Specific document to search (optional)
            top_k: Number of top results to return
            
        Returns:
            List of similar chunks with similarity scores
        """
        try:
            results = []
            
            # Determine which files to search
            if file_hash:
                files_to_search = [file_hash]
            else:
                # Get all documents with embeddings
                embedding_files = list(self.embeddings_dir.glob("*_embeddings.pkl"))
                files_to_search = [f.stem.replace("_embeddings", "") for f in embedding_files]
            
            for f_hash in files_to_search:
                embeddings = self.load_embeddings(f_hash)
                
                if not embeddings:
                    continue
                
                # Compute similarities
                similarities = []
                for emb in embeddings:
                    similarity = self.compute_similarity(query_embedding, emb.embedding)
                    similarities.append({
                        'chunk_id': emb.chunk_id,
                        'similarity': similarity,
                        'embedding_type': emb.embedding_type,
                        'metadata': emb.metadata
                    })
                
                # Sort by similarity
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                
                # Add top results
                for sim in similarities[:top_k]:
                    if sim['similarity'] > 0.1:  # Threshold
                        results.append({
                            'file_hash': f_hash,
                            'chunk_id': sim['chunk_id'],
                            'similarity': sim['similarity'],
                            'embedding_type': sim['embedding_type'],
                            'metadata': sim['metadata']
                        })
            
            # Sort all results by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []

# Initialize embedding service
embedding_service = EmbeddingService()

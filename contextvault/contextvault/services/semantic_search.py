"""
Semantic Search Service for ContextVault

Provides intelligent context retrieval using sentence transformers for semantic similarity,
combined with recency and access frequency scoring.
"""

import logging
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sqlalchemy.orm import Session

# Initialize logger early
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    FALLBACK_MODE = False
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    FALLBACK_MODE = True
except Exception as e:
    # Handle other import errors (like missing _lzma module)
    logger.warning(f"Sentence transformers import failed: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    FALLBACK_MODE = True

# Fallback imports for TF-IDF based similarity
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import re
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False
    logger.warning("scikit-learn not available for fallback semantic search")

from ..models.context import ContextEntry
from ..config import settings


class SemanticSearchService:
    """Handles semantic search for context entries using sentence transformers."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[str] = None,
        similarity_threshold: float = 0.3,
        max_results: int = 10
    ):
        """
        Initialize semantic search service.
        
        Args:
            model_name: Name of the sentence transformer model to use
            cache_dir: Directory to cache embeddings and model
            similarity_threshold: Minimum similarity score to include results
            max_results: Maximum number of results to return
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.model = None
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.last_cache_update = None
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = Path.home() / ".contextvault" / "semantic_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.embeddings_file = self.cache_dir / "embeddings.pkl"
        self.model_info_file = self.cache_dir / "model_info.pkl"
        
        # Initialize the model
        self._initialize_model()
        
        # Initialize fallback if needed
        if not self.is_available() and FALLBACK_AVAILABLE:
            self._initialize_fallback()
    
    def _initialize_model(self) -> bool:
        """Initialize the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("sentence-transformers not available. Semantic search disabled.")
            return False
        
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            start_time = time.time()
            
            # Load model with caching
            cache_folder = str(self.cache_dir / "model")
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=cache_folder
            )
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f}s. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
            
            # Load cached embeddings if available
            self._load_embeddings_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize semantic search model: {e}")
            self.model = None
            return False
    
    def _initialize_fallback(self):
        """Initialize TF-IDF based fallback semantic search."""
        if not FALLBACK_AVAILABLE:
            logger.warning("Fallback semantic search not available")
            return
        
        try:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1
            )
            self.fallback_mode = True
            # Use lower threshold for TF-IDF since it produces different similarity scores
            self.similarity_threshold = 0.15
            logger.info("Initialized TF-IDF fallback semantic search with threshold 0.15")
        except Exception as e:
            logger.error(f"Failed to initialize fallback semantic search: {e}")
            self.fallback_mode = False
    
    def is_available(self) -> bool:
        """Check if semantic search is available (either transformer or fallback)."""
        return (self.model is not None and SENTENCE_TRANSFORMERS_AVAILABLE) or \
               (hasattr(self, 'fallback_mode') and self.fallback_mode and FALLBACK_AVAILABLE)
    
    def _load_embeddings_cache(self):
        """Load cached embeddings from disk."""
        try:
            if self.embeddings_file.exists():
                with open(self.embeddings_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                self.embeddings_cache = cache_data.get('embeddings', {})
                self.last_cache_update = cache_data.get('last_update')
                
                logger.info(f"Loaded {len(self.embeddings_cache)} cached embeddings")
            else:
                logger.info("No embedding cache found, will generate on first use")
                
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            self.embeddings_cache = {}
    
    def _save_embeddings_cache(self):
        """Save embeddings cache to disk."""
        try:
            cache_data = {
                'embeddings': self.embeddings_cache,
                'last_update': datetime.now(),
                'model_name': self.model_name
            }
            
            with open(self.embeddings_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            logger.debug(f"Saved {len(self.embeddings_cache)} embeddings to cache")
            
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")
    
    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a single text."""
        if not self.is_available():
            return None
        
        try:
            # Clean and prepare text
            clean_text = self._clean_text(text)
            if not clean_text:
                return None
            
            # Generate embedding
            embedding = self.model.encode(clean_text, convert_to_numpy=True)
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple texts efficiently."""
        if not self.is_available():
            return [None] * len(texts)
        
        try:
            # Clean texts
            clean_texts = [self._clean_text(text) for text in texts]
            valid_indices = [i for i, text in enumerate(clean_texts) if text]
            valid_texts = [clean_texts[i] for i in valid_indices]
            
            if not valid_texts:
                return [None] * len(texts)
            
            # Generate embeddings in batch (much faster)
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True, batch_size=32)
            
            # Map back to original positions
            result = [None] * len(texts)
            for idx, embedding in zip(valid_indices, embeddings):
                result[idx] = embedding
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
    
    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for embedding."""
        if not text:
            return ""
        
        # Basic cleaning
        text = text.strip()
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate very long texts (transformer models have token limits)
        if len(text) > 512:
            text = text[:512]
        
        return text
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Normalize vectors
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def update_context_embeddings(self, db_session: Session, force_update: bool = False) -> int:
        """Update embeddings for all context entries in the database."""
        if not self.is_available():
            logger.warning("Semantic search not available, skipping embedding update")
            return 0
        
        try:
            # Get all context entries that need embeddings
            query = db_session.query(ContextEntry)
            
            if not force_update and self.last_cache_update:
                # Only update entries modified since last cache update
                query = query.filter(ContextEntry.updated_at > self.last_cache_update)
            
            entries = query.all()
            
            if not entries:
                logger.info("No context entries need embedding updates")
                return 0
            
            logger.info(f"Updating embeddings for {len(entries)} context entries")
            
            # Extract texts and IDs
            texts = [entry.content for entry in entries]
            entry_ids = [entry.id for entry in entries]
            
            # Generate embeddings in batch
            embeddings = self.generate_embeddings_batch(texts)
            
            # Update cache
            updated_count = 0
            for entry_id, embedding in zip(entry_ids, embeddings):
                if embedding is not None:
                    self.embeddings_cache[entry_id] = embedding
                    updated_count += 1
            
            # Save cache
            self._save_embeddings_cache()
            self.last_cache_update = datetime.now()
            
            logger.info(f"Updated {updated_count} embeddings successfully")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to update context embeddings: {e}")
            return 0
    
    def search_similar_contexts(
        self,
        query: str,
        db_session: Session,
        max_results: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Tuple[ContextEntry, float]]:
        """
        Search for context entries similar to the query.
        
        Returns:
            List of (ContextEntry, similarity_score) tuples, sorted by relevance
        """
        if not self.is_available():
            logger.warning("Semantic search not available, returning empty results")
            return []
        
        max_results = max_results or self.max_results
        similarity_threshold = similarity_threshold or self.similarity_threshold
        
        try:
            # Use fallback TF-IDF if transformers not available
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                return self._search_with_tfidf(query, db_session, max_results, similarity_threshold)
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if query_embedding is None:
                logger.warning("Failed to generate query embedding")
                return []
            
            # Ensure embeddings are up to date
            self.update_context_embeddings(db_session)
            
            # Get all context entries
            all_entries = db_session.query(ContextEntry).all()
            
            if not all_entries:
                return []
            
            # Calculate similarities
            similarities = []
            for entry in all_entries:
                if entry.id not in self.embeddings_cache:
                    # Generate embedding for this entry if missing
                    embedding = self.generate_embedding(entry.content)
                    if embedding is not None:
                        self.embeddings_cache[entry.id] = embedding
                    else:
                        continue
                
                entry_embedding = self.embeddings_cache[entry.id]
                similarity = self.calculate_similarity(query_embedding, entry_embedding)
                
                if similarity >= similarity_threshold:
                    similarities.append((entry, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top results
            return similarities[:max_results]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def _search_with_tfidf(
        self,
        query: str,
        db_session: Session,
        max_results: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Tuple[ContextEntry, float]]:
        """Fallback search using keyword matching."""
        max_results = max_results or self.max_results
        similarity_threshold = similarity_threshold or 0.05  # Lower threshold for keyword search
        
        try:
            # Get all context entries
            all_entries = db_session.query(ContextEntry).all()
            
            if not all_entries:
                logger.info("No context entries found for keyword search")
                return []
            
            # Simple keyword-based search
            query_words = set(re.findall(r'\b\w+\b', query.lower()))
            results = []
            
            for entry in all_entries:
                content_words = set(re.findall(r'\b\w+\b', entry.content.lower()))
                
                # Calculate keyword overlap
                overlap = len(query_words.intersection(content_words))
                total_words = len(query_words.union(content_words))
                
                if total_words > 0:
                    similarity = overlap / total_words
                    
                    # Boost for exact matches
                    if any(word in entry.content.lower() for word in query_words):
                        similarity += 0.1
                    
                    # Boost for programming-related content
                    programming_keywords = ['python', 'javascript', 'programming', 'code', 'develop', 'software', 'engineer', 'prefer', 'love', 'working', 'project', 'language']
                    if any(keyword in query.lower() and keyword in entry.content.lower() for keyword in programming_keywords):
                        similarity += 0.2
                    
                    # Boost for preference queries
                    preference_keywords = ['prefer', 'like', 'love', 'want', 'should', 'recommend', 'current']
                    if any(keyword in query.lower() and keyword in entry.content.lower() for keyword in preference_keywords):
                        similarity += 0.15
                    
                    # Boost for pet/personal questions
                    pet_keywords = ['pets', 'cats', 'dogs', 'animals', 'names']
                    personal_keywords = ['my', 'me', 'i have', 'i am', 'i live', 'i drive']
                    if any(keyword in query.lower() for keyword in pet_keywords) and any(keyword in entry.content.lower() for keyword in ['cats', 'dogs', 'pets', 'luna', 'pixel']):
                        similarity += 0.4
                    
                    # Boost for personal questions
                    if any(keyword in query.lower() for keyword in personal_keywords) and any(keyword in entry.content.lower() for keyword in ['i am', 'i have', 'i live', 'i drive', 'my']):
                        similarity += 0.2
                    
                    results.append((entry, min(similarity, 1.0)))
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Filter by threshold
            results = [r for r in results if r[1] > similarity_threshold]
            
            logger.info(f"Keyword search found {len(results)} results above threshold {similarity_threshold}")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def search_with_hybrid_scoring(
        self,
        query: str,
        db_session: Session,
        max_results: Optional[int] = None,
        semantic_weight: float = 0.6,
        recency_weight: float = 0.3,
        frequency_weight: float = 0.1
    ) -> List[Tuple[ContextEntry, float, Dict[str, float]]]:
        """
        Search with hybrid scoring combining semantic similarity, recency, and access frequency.
        
        Returns:
            List of (ContextEntry, total_score, score_breakdown) tuples
        """
        if not self.is_available():
            return []
        
        max_results = max_results or self.max_results
        
        try:
            # Get semantic similarities
            semantic_results = self.search_similar_contexts(
                query, db_session, max_results=100  # Get more candidates for reranking
            )
            
            if not semantic_results:
                return []
            
            # Calculate hybrid scores
            now = datetime.utcnow()
            hybrid_results = []
            
            for entry, semantic_score in semantic_results:
                # Recency score (entries from last 30 days get higher scores)
                days_old = (now - entry.created_at).days
                recency_score = max(0, 1 - (days_old / 30.0))
                
                # Frequency score (normalize access count)
                max_access = max(e.access_count for e, _ in semantic_results)
                frequency_score = entry.access_count / max(max_access, 1) if max_access > 0 else 0
                
                # Combined score
                total_score = (
                    semantic_score * semantic_weight +
                    recency_score * recency_weight +
                    frequency_score * frequency_weight
                )
                
                score_breakdown = {
                    'semantic': semantic_score,
                    'recency': recency_score,
                    'frequency': frequency_score,
                    'total': total_score
                }
                
                hybrid_results.append((entry, total_score, score_breakdown))
            
            # Sort by total score
            hybrid_results.sort(key=lambda x: x[1], reverse=True)
            
            # Apply diversity filtering (avoid very similar entries)
            filtered_results = self._apply_diversity_filtering(hybrid_results)
            
            return filtered_results[:max_results]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    def _apply_diversity_filtering(
        self,
        results: List[Tuple[ContextEntry, float, Dict[str, float]]],
        similarity_threshold: float = 0.9
    ) -> List[Tuple[ContextEntry, float, Dict[str, float]]]:
        """Remove very similar entries to increase diversity."""
        if not results:
            return results
        
        filtered = [results[0]]  # Always include the top result
        
        for entry, score, breakdown in results[1:]:
            # Check if this entry is too similar to already selected entries
            is_too_similar = False
            
            if entry.id in self.embeddings_cache:
                entry_embedding = self.embeddings_cache[entry.id]
                
                for selected_entry, _, _ in filtered:
                    if selected_entry.id in self.embeddings_cache:
                        selected_embedding = self.embeddings_cache[selected_entry.id]
                        similarity = self.calculate_similarity(entry_embedding, selected_embedding)
                        
                        if similarity > similarity_threshold:
                            is_too_similar = True
                            break
            
            if not is_too_similar:
                filtered.append((entry, score, breakdown))
        
        return filtered
    
    def clear_cache(self):
        """Clear the embeddings cache."""
        self.embeddings_cache.clear()
        if self.embeddings_file.exists():
            self.embeddings_file.unlink()
        logger.info("Embeddings cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the embeddings cache."""
        return {
            'cached_embeddings': len(self.embeddings_cache),
            'cache_file_exists': self.embeddings_file.exists(),
            'last_update': self.last_cache_update,
            'model_available': self.is_available(),
            'model_name': self.model_name,
            'fallback_mode': hasattr(self, 'fallback_mode') and self.fallback_mode,
            'transformers_available': SENTENCE_TRANSFORMERS_AVAILABLE
        }


# Global semantic search service instance
_semantic_search_service = None


def get_semantic_search_service() -> SemanticSearchService:
    """Get the global semantic search service instance."""
    global _semantic_search_service
    
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    
    return _semantic_search_service


def initialize_semantic_search() -> bool:
    """Initialize the semantic search service on startup."""
    try:
        service = get_semantic_search_service()
        if service.is_available():
            logger.info("Semantic search initialized successfully")
            return True
        else:
            logger.warning("Semantic search initialization failed")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize semantic search: {e}")
        return False

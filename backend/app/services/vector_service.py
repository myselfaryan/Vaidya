"""
Vector database service for medical document embeddings and retrieval.
"""

import json
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from functools import lru_cache

import pinecone
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger

from ..core.config import settings
from ..models.schemas import DocumentSearch
from ..utils.document_processor import DocumentProcessor


class VectorService:
    """Service for vector operations using Pinecone."""
    
    def __init__(self):
        """Initialize the vector service."""
        self.embedding_model = None
        self.index = None
        self.document_processor = DocumentProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self._initialize_pinecone()
        self._load_embedding_model()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index."""
        try:
            pinecone.init(
                api_key=settings.pinecone_api_key,
                environment=settings.pinecone_environment
            )
            
            # Create index if it doesn't exist
            if settings.pinecone_index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=settings.pinecone_index_name,
                    dimension=384,  # sentence-transformers dimension
                    metric="cosine"
                )
                logger.info(f"Created Pinecone index: {settings.pinecone_index_name}")
            
            self.index = pinecone.Index(settings.pinecone_index_name)
            logger.info("Pinecone initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def _load_embedding_model(self):
        """Load the sentence transformer model for embeddings."""
        try:
            # Use a medical domain-adapted model or general sentence transformer
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    @lru_cache(maxsize=1000)
    def _get_text_hash(self, text: str) -> str:
        """Generate a hash for text to use as cache key."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
        
    def generate_embeddings(
        self, 
        texts: List[str], 
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts with optional caching.
        
        Args:
            texts: List of text strings to embed
            use_cache: Whether to use cached embeddings if available
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []
                
            # Check cache for existing embeddings
            cached_embeddings = []
            uncached_texts = []
            text_to_idx = {}
            
            if use_cache:
                for i, text in enumerate(texts):
                    text_hash = self._get_text_hash(text)
                    if text_hash in self._embedding_cache:
                        cached_embeddings.append(self._embedding_cache[text_hash])
                    else:
                        uncached_texts.append(text)
                        text_to_idx[text] = i
            else:
                uncached_texts = texts
                text_to_idx = {text: i for i, text in enumerate(texts)}
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self.embedding_model.encode(
                    uncached_texts,
                    normalize_embeddings=True,
                    show_progress_bar=len(uncached_texts) > 10,
                    batch_size=32,
                    convert_to_numpy=True
                )
                
                if len(new_embeddings.shape) == 1:
                    new_embeddings = new_embeddings.reshape(1, -1)
                
                # Update cache
                for text, embedding in zip(uncached_texts, new_embeddings):
                    text_hash = self._get_text_hash(text)
                    self._embedding_cache[text_hash] = embedding.tolist()
                
                # Combine with cached embeddings
                if cached_embeddings:
                    all_embeddings = [None] * len(texts)
                    for text, idx in text_to_idx.items():
                        text_hash = self._get_text_hash(text)
                        all_embeddings[idx] = self._embedding_cache[text_hash]
                    return all_embeddings
                
                return new_embeddings.tolist()
                
            return cached_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = "medical-docs"
    ) -> bool:
        """
        Upsert vectors to Pinecone index.
        
        Args:
            vectors: List of vector dictionaries with id, values, and metadata
            namespace: Pinecone namespace
            
        Returns:
            Success status
        """
        try:
            # Upsert in batches to avoid timeout
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
            
            logger.info(f"Upserted {len(vectors)} vectors to namespace: {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            return False
    
    def search_similar(
        self,
        query_text: str,
        top_k: int = 5,
        namespace: str = "medical-docs",
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors based on query text.
        
        Args:
            query_text: Text to search for
            top_k: Number of results to return
            namespace: Pinecone namespace
            filter_dict: Metadata filters
            
        Returns:
            List of search results with metadata
        """
        try:
            # Generate embedding for query
            query_embedding = self.generate_embeddings([query_text])[0]
            
            # Search in Pinecone
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace,
                filter=filter_dict
            )
            
            # Process results
            results = []
            for match in search_results.matches:
                result = {
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": match.metadata,
                    "content": match.metadata.get("content", ""),
                    "source": match.metadata.get("source", ""),
                    "document_type": match.metadata.get("document_type", ""),
                    "title": match.metadata.get("title", "")
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} similar vectors for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar vectors: {e}")
            return []
    
    def delete_vectors(
        self,
        vector_ids: List[str],
        namespace: str = "medical-docs"
    ) -> bool:
        """
        Delete vectors from Pinecone index.
        
        Args:
            vector_ids: List of vector IDs to delete
            namespace: Pinecone namespace
            
        Returns:
            Success status
        """
        try:
            self.index.delete(ids=vector_ids, namespace=namespace)
            logger.info(f"Deleted {len(vector_ids)} vectors from namespace: {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    def get_index_stats(self, namespace: str = "medical-docs") -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.
        
        Args:
            namespace: Pinecone namespace
            
        Returns:
            Index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            
            namespace_stats = stats.namespaces.get(namespace, {})
            
            return {
                "total_vectors": stats.total_vector_count,
                "namespace_vectors": namespace_stats.get("vector_count", 0),
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespace": namespace
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}
    
    def process_document_for_vectors(
        self,
        document_id: str,
        text: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a document into vector-ready chunks with metadata.
        
        Args:
            document_id: Unique document identifier
            text: Document text content
            document_metadata: Additional document metadata
            
        Returns:
            List of vectors ready for upsert
        """
        # Process document into chunks
        chunks = self.document_processor.process_document(
            document_id=document_id,
            text=text,
            document_metadata=document_metadata
        )
        
        # Generate embeddings for chunks
        chunk_texts = [chunk['text'] for chunk in chunks]
        chunk_embeddings = self.generate_embeddings(chunk_texts)
        
        # Prepare vectors for Pinecone
        vectors = []
        for chunk, embedding in zip(chunks, chunk_embeddings):
            vector_id = f"{document_id}_{chunk['metadata']['chunk_index']}"
            
            vectors.append({
                'id': vector_id,
                'values': embedding,
                'metadata': {
                    **chunk['metadata'],
                    'text': chunk['text'],
                    'processed_at': datetime.utcnow().isoformat()
                }
            })
            
        return vectors
        """
        Process document chunks into vector format for Pinecone.
        
        Args:
            document_id: Unique document identifier
            chunks: List of document chunks with content
            document_metadata: Document metadata
            
        Returns:
            List of vectors ready for upsert
        """
        try:
            # Extract text content from chunks
            texts = [chunk["content"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Create vector objects
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{document_id}_{i}"
                
                metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk["content"],
                    "title": document_metadata.get("title", ""),
                    "document_type": document_metadata.get("document_type", ""),
                    "source": document_metadata.get("source", ""),
                    "authors": document_metadata.get("authors", []),
                    "publication_date": document_metadata.get("publication_date", ""),
                    "keywords": document_metadata.get("keywords", []),
                    "start_position": chunk.get("start_position", 0),
                    "end_position": chunk.get("end_position", 0),
                    "processed_at": datetime.utcnow().isoformat()
                }
                
                vector = {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                }
                vectors.append(vector)
            
            logger.info(f"Processed {len(vectors)} vectors for document: {document_id}")
            return vectors
            
        except Exception as e:
            logger.error(f"Failed to process document for vectors: {e}")
            return []
    
    def search_medical_knowledge(
        self,
        query: str,
        document_types: Optional[List[str]] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search medical knowledge base with filtering.
        
        Args:
            query: Medical query text
            document_types: Optional filter for document types
            max_results: Maximum number of results
            
        Returns:
            List of relevant medical information
        """
        try:
            # Build filter dictionary
            filter_dict = {}
            if document_types:
                filter_dict["document_type"] = {"$in": document_types}
            
            # Search for similar content
            results = self.search_similar(
                query_text=query,
                top_k=max_results,
                filter_dict=filter_dict if filter_dict else None
            )
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in results
                if result["score"] >= settings.similarity_threshold
            ]
            
            logger.info(f"Found {len(filtered_results)} relevant medical documents")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to search medical knowledge: {e}")
            return []
    
    def get_document_chunks(
        self,
        document_id: str,
        namespace: str = "medical-docs"
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.
        
        Args:
            document_id: Document identifier
            namespace: Pinecone namespace
            
        Returns:
            List of document chunks
        """
        try:
            # Use metadata filtering to get document chunks
            filter_dict = {"document_id": document_id}
            
            # Search with a dummy query but filter by document_id
            results = self.index.query(
                vector=[0.0] * 384,  # Dummy vector
                top_k=1000,  # Large number to get all chunks
                include_metadata=True,
                namespace=namespace,
                filter=filter_dict
            )
            
            chunks = []
            for match in results.matches:
                chunk = {
                    "id": match.id,
                    "content": match.metadata.get("content", ""),
                    "chunk_index": match.metadata.get("chunk_index", 0),
                    "start_position": match.metadata.get("start_position", 0),
                    "end_position": match.metadata.get("end_position", 0)
                }
                chunks.append(chunk)
            
            # Sort by chunk index
            chunks.sort(key=lambda x: x["chunk_index"])
            
            logger.info(f"Retrieved {len(chunks)} chunks for document: {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []


# Global vector service instance with LRU cache for embeddings
class CachedVectorService(VectorService):
    def __init__(self):
        super().__init__()
        self._embedding_cache = {}
        
    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        
    def get_cache_info(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'cache_size': len(self._embedding_cache),
            'cache_memory_usage': sum(
                len(str(key)) + sum(len(str(v)) for v in value)
                for key, value in self._embedding_cache.items()
            )
        }

# Initialize the vector service with caching
vector_service = CachedVectorService()

"""
Document processing utilities for medical text.
"""

import re
from typing import List, Dict, Any, Optional
from loguru import logger

class DocumentProcessor:
    """Utility class for processing medical documents into chunks."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize document text.
        
        Args:
            text: Raw document text
            
        Returns:
            Cleaned text
        """
        # Remove multiple whitespaces
        text = re.sub(r'\s+', ' ', text)
        # Normalize unicode characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        return text.strip()
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving medical abbreviations.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Common medical abbreviations that shouldn't end sentences
        medical_abbr = [
            'Dr.', 'Prof.', 'e.g.', 'i.e.', 'vs.', 'etc.', 'Fig.', 'fig.',
            'No.', 'vol.', 'sec.', 'ch.', 'pp.', 'p.', 'ed.', 'al.',
            'mmol/L', 'mg/dL', 'mEq/L', 'IU/L', 'U/L', 'mm[Hg]', 'kg/m²'
        ]
        
        # Create a pattern to match sentence boundaries
        pattern = r'(?<!(?:{}))(?:\s*[.!?]\s+|\s*\n\s*)(?=[A-Z0-9])'.format(
            '|'.join(map(re.escape, medical_abbr))
        )
        
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Split document into overlapping chunks with metadata.
        
        Args:
            text: Document text to chunk
            metadata: Additional metadata to include with each chunk
            
        Returns:
            List of chunks with metadata
        """
        if not text:
            return []
            
        # Clean the text first
        text = self.clean_text(text)
        
        # Split into sentences first
        sentences = self.split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunk_metadata = {
                    'chunk_id': chunk_id,
                    'chunk_length': len(chunk_text),
                    'is_continuation': chunk_id > 0,
                    **(metadata or {})
                }
                chunks.append({
                    'text': chunk_text,
                    'metadata': chunk_metadata
                })
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) // 2)
                current_chunk = current_chunk[overlap_start:]
                current_length = sum(len(s) for s in current_chunk) + len(current_chunk) - 1
                chunk_id += 1
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
        
        # Add the last chunk if not empty
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_metadata = {
                'chunk_id': chunk_id,
                'chunk_length': len(chunk_text),
                'is_continuation': chunk_id > 0,
                'is_last_chunk': True,
                **(metadata or {})
            }
            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    def process_document(
        self,
        document_id: str,
        text: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a complete document into chunks with metadata.
        
        Args:
            document_id: Unique document identifier
            text: Document text content
            document_metadata: Additional document metadata
            
        Returns:
            List of processed chunks ready for embedding
        """
        if not document_metadata:
            document_metadata = {}
            
        # Add document ID to metadata
        document_metadata['document_id'] = document_id
        
        # Chunk the document
        chunks = self.chunk_document(text, document_metadata)
        
        # Add chunk-specific metadata
        for i, chunk in enumerate(chunks):
            chunk['metadata']['chunk_index'] = i
            chunk['metadata']['total_chunks'] = len(chunks)
        
        return chunks

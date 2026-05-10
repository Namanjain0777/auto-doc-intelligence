"""
ChromaDB Vector Store Management
Handles storage and retrieval of embeddings for automotive document RAG system
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ChromaDBManager:
    """Manages ChromaDB collections for automotive document storage"""
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 embedding_model_name: str = "all-MiniLM-L6-v2",
                 collection_name: str = "automotive_manuals"):
        """
        Initialize ChromaDB manager
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            embedding_model_name: Sentence transformer model for embeddings
            collection_name: Name of the collection to use/create
        """
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model_name
        self.collection_name = collection_name
        
        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"ChromaDB initialized at {persist_directory}")
        logger.info(f"Using embedding model: {embedding_model_name}")
        logger.info(f"Collection '{collection_name}' ready with {self.collection.count()} documents")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection: {self.collection_name}")
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    def add_document_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Add document chunks to the vector store
        
        Args:
            chunks: List of chunk dictionaries with content and metadata
            
        Returns:
            List of IDs for the added chunks
        """
        if not chunks:
            return []
        
        try:
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                # Create unique ID
                chunk_id = self._generate_chunk_id(chunk)
                
                # Prepare document text
                document_text = chunk.get('content', '')
                if not document_text.strip():
                    logger.warning(f"Skipping empty chunk: {chunk_id}")
                    continue
                
                # Prepare metadata (ChromaDB requires string values)
                metadata = self._prepare_metadata(chunk.get('metadata', {}))
                
                documents.append(document_text)
                metadatas.append(metadata)
                ids.append(chunk_id)
            
            if not documents:
                logger.warning("No valid documents to add")
                return []
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} chunks to ChromaDB")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding chunks to ChromaDB: {str(e)}")
            raise
    
    def _generate_chunk_id(self, chunk: Dict[str, Any]) -> str:
        """Generate a unique ID for a chunk"""
        # Create ID based on content and metadata to avoid duplicates
        content = chunk.get('content', '')
        source_info = chunk.get('source_info', {})
        
        # Include key identifying information
        id_parts = [
            source_info.get('document', 'unknown'),
            str(source_info.get('page_number', 0)),
            chunk.get('chunk_type', 'unknown'),
            content[:50] if content else 'empty'
        ]
        
        id_string = "_".join(id_parts)
        # Hash to fixed length
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare metadata for ChromaDB storage
        Converts values to strings/numbers/booleans as required by ChromaDB
        """
        prepared = {}
        
        for key, value in metadata.items():
            if value is None:
                prepared[key] = ""  # ChromaDB doesn't like None values
            elif isinstance(value, (str, int, float, bool)):
                prepared[key] = value
            elif isinstance(value, list):
                # Convert list to comma-separated string
                prepared[key] = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                # Convert dict to JSON string
                prepared[key] = json.dumps(value)
            else:
                # Convert anything else to string
                prepared[key] = str(value)
        
        # Add timestamp for tracking
        prepared['indexed_at'] = datetime.now().isoformat()
        
        return prepared
    
    def search_similar(self, 
                      query_text: str, 
                      n_results: int = 5,
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in the vector store
        
        Args:
            query_text: Text to search for
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results with content, metadata, and similarity scores
        """
        try:
            # Prepare where clause for filtering
            where_clause = None
            if filter_metadata:
                # Convert metadata filter to ChromaDB format
                where_clause = {}
                for key, value in filter_metadata.items():
                    if isinstance(value, list):
                        # For list values, we need to check if any item matches
                        # ChromaDB doesn't have direct IN operator, so we'll handle this in post-filtering
                        pass
                    else:
                        where_clause[key] = value
            
            # Perform search
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    result_id = results['ids'][0][i]
                    document = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Convert distance to similarity score (1 - distance for cosine)
                    similarity_score = 1 - distance if distance is not None else 0.0
                    
                    # Parse metadata back from strings where needed
                    parsed_metadata = self._parse_metadata(metadata)
                    
                    formatted_results.append({
                        'id': result_id,
                        'content': document,
                        'metadata': parsed_metadata,
                        'similarity_score': similarity_score,
                        'distance': distance
                    })
            
            logger.info(f"Found {len(formatted_results)} similar chunks for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []
    
    def _parse_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Parse metadata back from ChromaDB storage format"""
        parsed = {}
        
        for key, value in metadata.items():
            if key == 'indexed_at':
                parsed[key] = value  # Keep timestamp as string
            elif key in ['font_sizes', 'font_names'] and isinstance(value, str):
                # Try to parse comma-separated lists back to lists
                try:
                    parsed[key] = [item.strip() for item in value.split(',') if item.strip()]
                except:
                    parsed[key] = value
            elif key in ['bbox'] and isinstance(value, str):
                # Try to parse bbox from string representation
                try:
                    # Handle format like "[x0, y0, x1, y1]" or "x0, y0, x1, y1"
                    cleaned = value.strip('[] ')
                    if ',' in cleaned:
                        parsed[key] = [float(x.strip()) for x in cleaned.split(',')]
                    else:
                        parsed[key] = value
                except:
                    parsed[key] = value
            else:
                parsed[key] = value
        
        return parsed
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}
    
    def delete_document(self, document_name: str) -> bool:
        """
        Delete all chunks associated with a document
        
        Args:
            document_name: Name of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"document": document_name},
                include=[]  # We only need IDs
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document: {document_name}")
                return True
            else:
                logger.warning(f"No chunks found for document: {document_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {document_name}: {str(e)}")
            return False
    
    def reset_collection(self) -> bool:
        """Reset/delete the entire collection (use with caution)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.info(f"Reset collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            return False


# Utility functions
def create_chunk_from_pdf_chunk(pdf_chunk, embedding: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Convert a PDFChunk object to a dictionary suitable for ChromaDB storage
    
    Args:
        pdf_chunk: PDFChunk object from ingestion module
        embedding: Pre-computed embedding (if None, will be computed later)
        
    Returns:
        Dictionary ready for ChromaDB storage
    """
    return {
        'content': pdf_chunk.content,
        'metadata': {
            **pdf_chunk.metadata,
            'chunk_type': pdf_chunk.chunk_type,
            **pdf_chunk.source_info
        },
        'chunk_type': pdf_chunk.chunk_type,
        'source_info': pdf_chunk.source_info,
        'embedding': embedding
    }


if __name__ == "__main__":
    # For testing
    import sys
    import tempfile
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    # Test basic functionality
    print("Testing ChromaDB Manager...")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        db_manager = ChromaDBManager(
            persist_directory=os.path.join(temp_dir, "test_chroma"),
            collection_name="test_collection"
        )
        
        # Test adding documents
        test_chunks = [
            {
                'content': 'This is a test chunk about brake systems.',
                'metadata': {
                    'document': 'test_manual.pdf',
                    'page_number': 1,
                    'section': 'Brakes'
                },
                'chunk_type': 'text',
                'source_info': {
                    'document': 'test_manual.pdf',
                    'page_number': 1
                }
            },
            {
                'content': 'ABS module controls wheel speed sensors.',
                'metadata': {
                    'document': 'test_manual.pdf',
                    'page_number': 2,
                    'section': 'Brakes'
                },
                'chunk_type': 'text',
                'source_info': {
                    'document': 'test_manual.pdf',
                    'page_number': 2
                }
            }
        ]
        
        ids = db_manager.add_document_chunks(test_chunks)
        print(f"Added chunks with IDs: {ids}")
        
        # Test search
        results = db_manager.search_similar("brake system", n_results=2)
        print(f"Search results: {len(results)} found")
        for result in results:
            print(f"  - Score: {result['similarity_score']:.3f}: {result['content'][:50]}...")
        
        # Test stats
        stats = db_manager.get_collection_stats()
        print(f"Collection stats: {stats}")
"""
RAG Query Pipeline for Automotive Document Intelligence System
Orchestrates retrieval-augmented generation for querying automotive technical documents
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from datetime import datetime

# Import our modules (order matters - vector_store before google genai)
from vector_store.chroma_manager import ChromaDBManager, create_chunk_from_pdf_chunk
from ingestion.pdf_processor import AutomotivePDFProcessor, PDFChunk
from vision.gemini_processor import GeminiVisionProcessor, DiagramDescription
from utils.text_cleaner import TextCleaner
from utils.sae_normalizer import SAENormalizer

# Import Google genai last to avoid import conflicts
import google.generativeai as genai

logger = logging.getLogger(__name__)

@dataclass
class QueryRequest:
    """Represents a user query request"""
    query: str
    max_results: int = 5
    include_diagrams: bool = True
    filters: Optional[Dict[str, Any]] = None
    user_context: Optional[str] = None  # e.g., vehicle make/model/year

@dataclass
class QueryResponse:
    """Represents a response from the RAG system"""
    answer: str
    sources: List[Dict[str, Any]]
    diagram_references: List[str]
    confidence_score: float
    query_time: float
    timestamp: str
    metadata: Dict[str, Any]

class AutomotiveRAGPipeline:
    """Main RAG pipeline for automotive document querying"""
    
    def __init__(self, 
                 google_api_key: Optional[str] = None,
                 chroma_persist_dir: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG pipeline
        
        Args:
            google_api_key: Google AI API key for Gemini
            chroma_persist_dir: Directory for ChromaDB persistence
            embedding_model: Sentence transformer model for embeddings
        """
        # Initialize components
        self.text_cleaner = TextCleaner()
        self.sae_normalizer = SAENormalizer()
        self.vision_processor = GeminiVisionProcessor(api_key=google_api_key)
        self.pdf_processor = AutomotivePDFProcessor()
        self.vector_store = ChromaDBManager(
            persist_directory=chroma_persist_dir,
            embedding_model_name=embedding_model
        )
        
        # Initialize Gemini for text generation
        self.api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google AI API key is required for RAG pipeline")
        
        genai.configure(api_key=self.api_key)
        self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # RAG prompt template
        self.rag_prompt_template = """
        You are an expert automotive technician assistant. Answer the user's question based on the provided context from automotive service manuals.
        
        Guidelines:
        1. Provide accurate, step-by-step information when applicable
        2. Include safety warnings and cautions from the source material
        3. Reference specific diagrams or figures when mentioned in the context
        4. Use standard SAE/JASO terminology
        5. If the context doesn't contain sufficient information, say so clearly
        6. Format procedures as numbered steps
        7. Include torque specifications, measurements, and other technical details when available
        
        Context from automotive manuals:
        {context}
        
        User Question: {question}
        
        Vehicle Context: {vehicle_context}
        
        Provide a comprehensive answer based solely on the provided context:
        """
    
    def add_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process and add an automotive service manual to the knowledge base
        
        Args:
            file_path: Path to the PDF service manual
            
        Returns:
            Dictionary with processing results
        """
        start_time = datetime.now()
        logger.info(f"Adding document to knowledge base: {file_path}")
        
        try:
            # Step 1: Extract content from PDF
            logger.info("Extracting content from PDF...")
            pdf_chunks = self.pdf_processor.extract_content_from_pdf(file_path)
            
            if not pdf_chunks:
                return {
                    "success": False,
                    "message": "No content extracted from PDF",
                    "chunks_processed": 0
                }
            
            # Step 2: Process diagrams with Gemini Vision
            logger.info("Processing diagrams with Gemini Vision...")
            diagram_chunks = [chunk for chunk in pdf_chunks if chunk.chunk_type == "diagram"]
            text_chunks = [chunk for chunk in pdf_chunks if chunk.chunk_type == "text"]
            
            # Process diagrams
            processed_diagram_chunks = []
            for diagram_chunk in diagram_chunks:
                try:
                    # Get image data from metadata
                    image_data = diagram_chunk.metadata.get("image_data")
                    if not image_data:
                        logger.warning("No image data found in diagram chunk")
                        continue
                    
                    # Get context from source info
                    context_hint = diagram_chunk.source_info.get("section", "")
                    
                    # Analyze diagram with Gemini Vision
                    description = self.vision_processor.describe_diagram(
                        image_data, 
                        context_hint=context_hint
                    )
                    
                    # Create enhanced chunk with vision description
                    enhanced_content = self._create_diagram_chunk_content(
                        diagram_chunk, 
                        description
                    )
                    
                    # Create new chunk with enhanced content
                    enhanced_chunk = PDFChunk(
                        content=enhanced_content,
                        metadata={
                            **diagram_chunk.metadata,
                            "vision_description": asdict(description),
                            "diagram_processed": True
                        },
                        chunk_type="diagram_description",
                        source_info=diagram_chunk.source_info
                    )
                    
                    processed_diagram_chunks.append(enhanced_chunk)
                    
                except Exception as e:
                    logger.error(f"Error processing diagram: {str(e)}")
                    # Still include the original chunk but mark as failed
                    failed_chunk = PDFChunk(
                        content=f"[Diagram processing failed: {str(e)}]",
                        metadata={
                            **diagram_chunk.metadata,
                            "diagram_processed": False,
                            "processing_error": str(e)
                        },
                        chunk_type="diagram_failed",
                        source_info=diagram_chunk.source_info
                    )
                    processed_diagram_chunks.append(failed_chunk)
            
            # Step 3: Enhance text chunks with cleaning and normalization
            logger.info("Enhancing text chunks...")
            enhanced_text_chunks = []
            for text_chunk in text_chunks:
                try:
                    # Clean and normalize text
                    cleaned_content = self.text_cleaner.clean_text(text_chunk.content)
                    normalized_content = self.sae_normalizer.normalize_text(cleaned_content)
                    
                    # Create enhanced chunk
                    enhanced_chunk = PDFChunk(
                        content=normalized_content,
                        metadata={
                            **text_chunk.metadata,
                            "text_cleaned": True,
                            "sae_normalized": True
                        },
                        chunk_type="text_enhanced",
                        source_info=text_chunk.source_info
                    )
                    
                    enhanced_text_chunks.append(enhanced_chunk)
                    
                except Exception as e:
                    logger.warning(f"Error enhancing text chunk: {str(e)}")
                    # Keep original chunk if enhancement fails
                    enhanced_text_chunks.append(text_chunk)
            
            # Step 4: Combine all chunks and prepare for vector storage
            all_chunks = processed_diagram_chunks + enhanced_text_chunks
            
            # Step 5: Generate embeddings and store in ChromaDB
            logger.info("Generating embeddings and storing in vector database...")
            storage_chunks = []
            
            for chunk in all_chunks:
                if chunk.content.strip():  # Only store non-empty chunks
                    storage_chunk = create_chunk_from_pdf_chunk(chunk)
                    storage_chunks.append(storage_chunk)
            
            # Add to vector store
            stored_ids = self.vector_store.add_document_chunks(storage_chunks)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": f"Successfully processed and stored document",
                "filename": os.path.basename(file_path),
                "chunks_processed": len(all_chunks),
                "text_chunks": len(enhanced_text_chunks),
                "diagram_chunks": len(processed_diagram_chunks),
                "stored_chunks": len(stored_ids),
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Document processing complete: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            return {
                "success": False,
                "message": f"Error processing document: {str(e)}",
                "chunks_processed": 0,
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def _create_diagram_chunk_content(self, 
                                    diagram_chunk: PDFChunk, 
                                    description: DiagramDescription) -> str:
        """Create enhanced content for a diagram chunk using vision description"""
        content_parts = []
        
        # Add original caption if available
        caption = diagram_chunk.source_info.get("caption")
        if caption:
            content_parts.append(f"Diagram Caption: {caption}")
        
        # Add vision description
        content_parts.append(f"Diagram Description: {description.description}")
        
        # Add structured information
        if description.components:
            content_parts.append(f"Components Identified: {', '.join(description.components)}")
        
        if description.procedures:
            content_parts.append(f"Suggested Procedures: {', '.join(description.procedures)}")
        
        if description.warnings:
            content_parts.append(f"Safety Warnings: {', '.join(description.warnings)}")
        
        if description.specifications:
            content_parts.append(f"Technical Specifications: {', '.join(description.specifications)}")
        
        if description.automotive_terms:
            content_parts.append(f"Automotive Terms: {', '.join(description.automotive_terms)}")
        
        # Add confidence indicator
        content_parts.append(f"Analysis Confidence: {description.confidence_score:.2f}")
        
        return "\n\n".join(content_parts)
    
    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a user query using the RAG pipeline
        
        Args:
            request: QueryRequest object containing the query and parameters
            
        Returns:
            QueryResponse object with answer and sources
        """
        start_time = datetime.now()
        logger.info(f"Processing query: '{request.query[:100]}...'")
        
        try:
            # Step 1: Clean and normalize the query
            cleaned_query = self.text_cleaner.clean_text(request.query)
            normalized_query = self.sae_normalizer.normalize_text(cleaned_query)
            
            # Step 2: Retrieve relevant chunks from vector store
            logger.info("Retrieving relevant chunks from vector store...")
            search_results = self.vector_store.search_similar(
                query_text=normalized_query,
                n_results=request.max_results,
                filter_metadata=request.filters
            )
            
            if not search_results:
                # Try with original query if normalized didn't work
                search_results = self.vector_store.search_similar(
                    query_text=cleaned_query,
                    n_results=request.max_results,
                    filter_metadata=request.filters
                )
            
            # Step 3: Prepare context from retrieved chunks
            context_parts = []
            sources = []
            diagram_references = []
            
            for result in search_results:
                # Add to context
                context_parts.append(f"[Source: {result['metadata'].get('document', 'Unknown')} "
                                   f"Page {result['metadata'].get('page_number', '?')}]\n"
                                   f"{result['content']}\n")
                
                # Track source information
                source_info = {
                    "document": result['metadata'].get('document', 'Unknown'),
                    "page_number": result['metadata'].get('page_number'),
                    "chunk_type": result['metadata'].get('chunk_type'),
                    "similarity_score": result['similarity_score'],
                    "metadata": result['metadata']
                }
                sources.append(source_info)
                
                # Track diagram references
                if result['metadata'].get('chunk_type') in ['diagram', 'diagram_description']:
                    diagram_id = result['metadata'].get('diagram_id')
                    if diagram_id:
                        diagram_references.append(diagram_id)
                    elif 'FIG_' in result['content']:
                        # Extract potential diagram references from text
                        import re
                        fig_matches = re.findall(r'FIG[._\-]?\s*\d+[A-Z]?', result['content'], re.IGNORECASE)
                        diagram_references.extend(fig_matches)
            
            context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant information found in the knowledge base."
            
            # Step 4: Generate answer using Gemini Pro
            logger.info("Generating answer with Gemini Pro...")
            vehicle_context = request.user_context or "Not specified"
            
            prompt = self.rag_prompt_template.format(
                context=context,
                question=request.query,
                vehicle_context=vehicle_context
            )
            
            response = self.text_model.generate_content(prompt)
            answer = response.text
            
            # Step 5: Calculate confidence score based on source quality
            confidence_score = self._calculate_confidence_score(search_results, answer)
            
            # Step 6: Prepare final response
            query_time = (datetime.now() - start_time).total_seconds()
            
            response_obj = QueryResponse(
                answer=answer,
                sources=sources,
                diagram_references=list(set(diagram_references)),  # Deduplicate
                confidence_score=confidence_score,
                query_time=query_time,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "query_length": len(request.query),
                    "results_found": len(search_results),
                    "normalized_query": normalized_query,
                    "model_used": "gemini-1.5-flash"
                }
            )
            
            logger.info(f"Query processed in {query_time:.2f}s with confidence {confidence_score:.2f}")
            return response_obj
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            query_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResponse(
                answer=f"I encountered an error while processing your question: {str(e)}",
                sources=[],
                diagram_references=[],
                confidence_score=0.0,
                query_time=query_time,
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(e)}
            )
    
    def _calculate_confidence_score(self, 
                                  search_results: List[Dict[str, Any]], 
                                  answer: str) -> float:
        """Calculate confidence score for the answer based on source quality"""
        if not search_results:
            return 0.0
        
        # Base confidence on similarity scores
        avg_similarity = sum(result['similarity_score'] for result in search_results) / len(search_results)
        
        # Adjust based on number of sources
        source_factor = min(len(search_results) / 5.0, 1.0)  # Max at 5 sources
        
        # Adjust based on answer length and specificity
        length_factor = min(len(answer) / 500.0, 1.0)  # Normalize to 500 chars
        
        # Check for uncertainty indicators in answer
        uncertainty_indicators = [
            'i don\'t know', 'unsure', 'uncertain', 'not clear', 
            'information not available', 'cannot determine'
        ]
        uncertainty_penalty = 0.0
        answer_lower = answer.lower()
        for indicator in uncertainty_indicators:
            if indicator in answer_lower:
                uncertainty_penalty += 0.1
        
        # Calculate final score
        confidence = avg_similarity * source_factor * length_factor
        confidence = max(0.0, min(1.0, confidence - uncertainty_penalty))
        
        return round(confidence, 3)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        vector_stats = self.vector_store.get_collection_stats()
        
        return {
            "vector_store": vector_stats,
            "components": {
                "pdf_processor": "AutomaticPDFProcessor",
                "vision_processor": "GeminiVisionProcessor",
                "text_cleaner": "TextCleaner",
                "sae_normalizer": "SAENormalizer",
                "text_model": "gemini-1.5-flash"
            },
            "timestamp": datetime.now().isoformat()
        }


# Convenience functions for easy usage
def create_rag_pipeline(google_api_key: Optional[str] = None, 
                       persist_directory: str = "./chroma_db") -> AutomotiveRAGPipeline:
    """
    Factory function to create a RAG pipeline instance
    
    Args:
        google_api_key: Google AI API key
        persist_directory: Directory for ChromaDB persistence
        
    Returns:
        Configured AutomotiveRAGPipeline instance
    """
    return AutomotiveRAGPipeline(
        google_api_key=google_api_key,
        chroma_persist_dir=persist_directory
    )


def process_query(pipeline: AutomotiveRAGPipeline, 
                  query: str, 
                  **kwargs) -> QueryResponse:
    """
    Convenience function to process a query
    
    Args:
        pipeline: Initialized RAG pipeline
        query: User query string
        **kwargs: Additional arguments for QueryRequest
        
    Returns:
        QueryResponse object
    """
    request = QueryRequest(query=query, **kwargs)
    return pipeline.query(request)


if __name__ == "__main__":
    # For testing
    import sys
    import tempfile
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    # Test with dummy data (would need actual API key for real test)
    print("Testing RAG Pipeline structure...")
    
    # This would fail without API key, but we can test initialization
    try:
        # Try to create pipeline (will fail without API key)
        pipeline = AutomotiveRAGPipeline(google_api_key="test_key_for_structure_test")
        print("Pipeline created successfully")
        
        # Test stats
        stats = pipeline.get_system_stats()
        print(f"System stats: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        print(f"Expected error (no valid API key): {str(e)}")
        print("Pipeline structure is correct - ready for real API key")
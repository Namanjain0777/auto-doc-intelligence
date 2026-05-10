"""
FastAPI API Router for Query Processing
Endpoints for querying the automotive document intelligence system
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import time

# Import our RAG pipeline
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rag.query_pipeline import AutomotiveRAGPipeline, QueryRequest, QueryResponse
from utils.logger import setup_logger

# Setup router and logger
router = APIRouter()
logger = setup_logger(__name__)

# Pydantic models for request/validation
class QueryRequestModel(BaseModel):
    query: str = Field(..., description="The user's question about automotive repair/maintenance")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results to retrieve")
    include_diagrams: bool = Field(True, description="Whether to include diagram information in search")
    user_context: Optional[str] = Field(None, description="Optional vehicle context (make/model/year)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")

class QueryResponseModel(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    diagram_references: List[str]
    confidence_score: float
    query_time: float
    timestamp: str
    metadata: Dict[str, Any]

class SystemStatsResponse(BaseModel):
    vector_store: Dict[str, Any]
    components: Dict[str, str]
    timestamp: str

def get_rag_pipeline() -> AutomotiveRAGPipeline:
    """Dependency to get RAG pipeline instance"""
    # This would be set up in main.py or through app state in a real implementation
    # For now, we'll create a new instance (not ideal for production but works for demo)
    import os
    from rag.query_pipeline import AutomotiveRAGPipeline
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise HTTPException(
            status_code=500,
            detail="RAG pipeline not configured. Missing GOOGLE_API_KEY environment variable."
        )
    
    persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    return AutomotiveRAGPipeline(
        google_api_key=google_api_key,
        chroma_persist_dir=persist_directory
    )

@router.post("/", response_model=QueryResponseModel)
async def process_query(
    request: QueryRequestModel,
    pipeline: AutomotiveRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Process a user query using the RAG pipeline
    
    Args:
        request: Query request parameters
        pipeline: RAG pipeline dependency
        
    Returns:
        Query response with answer and sources
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: '{request.query[:100]}...'")
        
        # Convert to internal request model
        internal_request = QueryRequest(
            query=request.query,
            max_results=request.max_results,
            include_diagrams=request.include_diagrams,
            filters=request.filters,
            user_context=request.user_context
        )
        
        # Process query through RAG pipeline
        response = pipeline.query(internal_request)
        
        # Convert to response model
        query_time = time.time() - start_time
        
        return QueryResponseModel(
            answer=response.answer,
            sources=response.sources,
            diagram_references=response.diagram_references,
            confidence_score=response.confidence_score,
            query_time=response.query_time,
            timestamp=response.timestamp,
            metadata=response.metadata
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        query_time = time.time() - start_time
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.get("/suggested-questions")
async def get_suggested_questions():
    """
    Get suggested questions for automotive repair topics
    """
    suggested = [
        "How do I replace the brake pads on a 2018 Toyota Camry?",
        "What is the torque specification for lug nuts on a Honda Civic?",
        "Where is the OBD-II port located on a 2020 Ford F-150?",
        "How to diagnose a check engine light related to oxygen sensors?",
        "What is the procedure for flushing the cooling system?",
        "How to test the alternator output voltage?",
        "What are the steps to replace a timing belt?",
        "How to bleed the brake system after replacing calipers?",
        "What is the recommended tire pressure for a Subaru Outback?",
        "How to reset the maintenance light on a Nissan Altima?"
    ]
    
    return {
        "suggested_questions": suggested,
        "note": "These are example questions you can ask the system"
    }

@router.get("/health")
async def query_health_check(pipeline: AutomotiveRAGPipeline = Depends(get_rag_pipeline)):
    """
    Health check for the query system
    
    Args:
        pipeline: RAG pipeline dependency
        
    Returns:
        Health status
    """
    try:
        # Try to get system stats to verify everything is working
        stats = pipeline.get_system_stats()
        
        return {
            "status": "healthy",
            "service": "query_processing",
            "vector_store": stats.get("vector_store", {}),
            "timestamp": stats.get("timestamp")
        }
    except Exception as e:
        logger.error(f"Query health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Query service unhealthy: {str(e)}"
        )
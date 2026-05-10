"""
FastAPI API Router for Document Management
Endpoints for uploading and processing automotive service manuals
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import os
import logging
from typing import Dict, Any, Optional
import shutil
from pathlib import Path

# Import our RAG pipeline
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from rag.query_pipeline import AutomotiveRAGPipeline, QueryResponse
from utils.logger import setup_logger

# Setup router and logger
router = APIRouter()
logger = setup_logger(__name__)

# Global RAG pipeline instance (in production, use dependency injection or app state)
rag_pipeline: Optional[AutomotiveRAGPipeline] = None

def get_rag_pipeline() -> AutomotiveRAGPipeline:
    """Dependency to get RAG pipeline instance"""
    global rag_pipeline
    if rag_pipeline is None:
        # Initialize with environment variables
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500, 
                detail="RAG pipeline not configured. Missing GOOGLE_API_KEY environment variable."
            )
        
        persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        rag_pipeline = AutomotiveRAGPipeline(
            google_api_key=google_api_key,
            chroma_persist_dir=persist_directory
        )
        logger.info("RAG pipeline initialized")
    
    return rag_pipeline

@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pipeline: AutomotiveRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Upload and process an automotive service manual PDF
    
    Args:
        file: PDF file to upload
        background_tasks: FastAPI background tasks
        pipeline: RAG pipeline dependency
        
    Returns:
        Processing results
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    # Validate file size (limit to 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    contents = await file.read()
    
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
        )
    
    # Reset file position for potential reuse
    await file.seek(0)
    
    logger.info(f"Received upload: {file.filename} ({len(contents)} bytes)")
    
    # Save uploaded file temporarily
    upload_dir = Path("./uploads")
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved uploaded file to: {file_path}")
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            str(file_path),
            pipeline
        )
        
        return {
            "message": f"File '{file.filename}' uploaded successfully. Processing started in background.",
            "filename": file.filename,
            "size_bytes": len(contents),
            "status": "processing",
            "note": "Check /documents/status for processing completion"
        }
        
    except Exception as e:
        logger.error(f"Error handling upload {file.filename}: {str(e)}")
        # Clean up temp file if it exists
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing upload: {str(e)}"
        )

async def process_document_background(file_path: str, pipeline: AutomotiveRAGPipeline):
    """Background task to process uploaded document"""
    try:
        logger.info(f"Starting background processing of: {file_path}")
        result = pipeline.add_document(file_path)
        logger.info(f"Background processing complete: {result}")
        
        # Optionally, you could store results in a database or send notifications
        # For now, we just log the result
        
    except Exception as e:
        logger.error(f"Error in background processing of {file_path}: {str(e)}")
    finally:
        # Clean up uploaded file after processing (optional)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not remove temporary file {file_path}: {str(e)}")

@router.get("/status")
async def get_processing_status():
    """
    Get status of document processing (simplified)
    In a production system, this would check a job queue or database
    """
    # This is a simplified implementation
    # In reality, you'd track processing jobs in a database or queue
    return {
        "status": "system_ready",
        "message": "Document processing system is operational",
        "note": "For detailed job tracking, implement a job queue system"
    }

@router.get("/collections")
async def get_collection_info(pipeline: AutomotiveRAGPipeline = Depends(get_rag_pipeline)):
    """
    Get information about the document collection
    
    Args:
        pipeline: RAG pipeline dependency
        
    Returns:
        Collection statistics
    """
    try:
        stats = pipeline.get_system_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting collection info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving collection information: {str(e)}"
        )

@router.delete("/collections/{document_name}")
async def delete_document(
    document_name: str,
    pipeline: AutomotiveRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Delete a document from the knowledge base
    
    Args:
        document_name: Name of the document to delete
        pipeline: RAG pipeline dependency
        
    Returns:
        Deletion result
    """
    try:
        success = pipeline.vector_store.delete_document(document_name)
        
        if success:
            return {
                "message": f"Document '{document_name}' successfully deleted from knowledge base",
                "document": document_name,
                "status": "deleted"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_name}' not found in knowledge base"
            )
            
    except Exception as e:
        logger.error(f"Error deleting document {document_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@router.post("/reset")
async def reset_knowledge_base(
    pipeline: AutomotiveRAGPipeline = Depends(get_rag_pipeline)
):
    """
    Reset/clear the entire knowledge base (use with caution)
    
    Args:
        pipeline: RAG pipeline dependency
        
    Returns:
        Reset result
    """
    try:
        success = pipeline.vector_store.reset_collection()
        
        if success:
            return {
                "message": "Knowledge base successfully reset",
                "status": "reset",
                "warning": "All documents have been removed from the system"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset knowledge base"
            )
            
    except Exception as e:
        logger.error(f"Error resetting knowledge base: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting knowledge base: {str(e)}"
        )
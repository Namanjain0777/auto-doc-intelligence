"""
Automotive Document Intelligence System
Main FastAPI Application Entry Point
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Get the frontend directory
FRONTEND_DIR = Path(__file__).parent / "frontend"

# Load environment variables
load_dotenv()

# Setup logger (lightweight)
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Automotive Document Intelligence System",
    description="A RAG-powered system for querying automotive service manuals",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Lazy imports - only load when endpoints are called
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Automotive Document Intelligence System")
    # Import routers here to avoid loading heavy modules at startup
    from api import document_router, query_router
    app.include_router(document_router.router, prefix="/api/documents", tags=["documents"])
    app.include_router(query_router.router, prefix="/api/query", tags=["query"])
    logger.info("Routes loaded successfully")

@app.get("/")
async def root():
    """Serve the frontend"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "vector_store": "lazy_loaded",
            "vision_api": "lazy_loaded"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
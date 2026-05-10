"""
Configuration Management
Centralized configuration for the Automotive Document Intelligence System
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AppConfig:
    """Application configuration settings"""
    
    # API Settings
    app_name: str = "Automotive Document Intelligence System"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    port: int = int(os.getenv("PORT", "8000"))
    
    # API Keys
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Vector Database
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Document Processing
    pdf_dpi: int = int(os.getenv("PDF_DPI", "300"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # RAG Settings
    max_retrieval_results: int = int(os.getenv("MAX_RETRIEVAL_RESULTS", "5"))
    min_similarity_threshold: float = float(os.getenv("MIN_SIMILARITY_THRESHOLD", "0.3"))
    
    # Processing
    batch_size: int = int(os.getenv("BATCH_SIZE", "10"))
    max_workers: int = int(os.getenv("MAX_WORKERS", "4"))
    
    # Paths
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    temp_dir: str = os.getenv("TEMP_DIR", "./temp")
    logs_dir: str = os.getenv("LOGS_DIR", "./logs")
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))
    
    # Rate Limiting (if implemented)
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    def __post_init__(self):
        """Post-initialization setup"""
        # Ensure directories exist
        self._ensure_directories()
        
        # Validate required settings
        self._validate_config()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            self.chroma_persist_dir,
            self.upload_dir,
            self.temp_dir,
            self.logs_dir,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self):
        """Validate required configuration"""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required")
        
        if self.chunk_size < 100:
            raise ValueError("CHUNK_SIZE must be at least 100")
        
        if self.port < 1024 or self.port > 65535:
            raise ValueError("PORT must be between 1024 and 65535")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive values)"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "debug": self.debug,
            "environment": self.environment,
            "port": self.port,
            "embedding_model": self.embedding_model,
            "chroma_persist_dir": self.chroma_persist_dir,
            "pdf_dpi": self.pdf_dpi,
            "chunk_size": self.chunk_size,
            "max_file_size_mb": self.max_file_size_mb,
            "max_retrieval_results": self.max_retrieval_results,
            "rate_limit_per_minute": self.rate_limit_per_minute,
        }
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create configuration from environment variables"""
        return cls()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"


class Config:
    """Singleton configuration instance"""
    _instance: Optional[AppConfig] = None
    
    @classmethod
    def get(cls) -> AppConfig:
        """Get the configuration instance"""
        if cls._instance is None:
            cls._instance = AppConfig.from_env()
        return cls._instance


# Convenience function to get config
def get_config() -> AppConfig:
    """Get application configuration"""
    return Config.get()


if __name__ == "__main__":
    # Test configuration
    try:
        config = AppConfig.from_env()
        print("Configuration loaded successfully:")
        print(config.to_dict())
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Make sure to set GOOGLE_API_KEY in your .env file")
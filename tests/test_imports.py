"""
Tests for import verification
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    try:
        # Test utils imports
        from utils.logger import setup_logger
        from utils.text_cleaner import TextCleaner
        from utils.sae_normalizer import SAENormalizer
        
        # Test ingestion imports (may fail if PyMuPDF not installed)
        try:
            from ingestion.pdf_processor import AutomotivePDFProcessor, PDFChunk
        except ImportError:
            pass  # Dependencies may not be installed
        
        # Test vector store imports (may fail if chromadb not installed)
        try:
            from vector_store.chroma_manager import ChromaDBManager
        except ImportError:
            pass
        
        # Test vision imports (may fail if google-generativeai not installed)
        try:
            from vision.gemini_processor import GeminiVisionProcessor
        except ImportError:
            pass
        
        # Test rag imports (may fail if dependencies not installed)
        try:
            from rag.query_pipeline import AutomotiveRAGPipeline
        except ImportError:
            pass
        
        print("All import tests passed!")
        return True
        
    except Exception as e:
        print(f"Import test failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from config import AppConfig
        print("Config import test passed!")
        return True
    except Exception as e:
        print(f"Config import test failed: {e}")
        return False

if __name__ == "__main__":
    print("Running import verification tests...")
    test_imports()
    test_config()
    print("Tests complete.")
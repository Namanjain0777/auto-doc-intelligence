"""
Ingestion module for processing automotive PDFs
"""

from .pdf_processor import AutomotivePDFProcessor, PDFChunk, TextBlock, DiagramInfo

__all__ = ['AutomotivePDFProcessor', 'PDFChunk', 'TextBlock', 'DiagramInfo']
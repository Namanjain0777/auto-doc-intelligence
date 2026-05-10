"""
API module for FastAPI endpoints
"""

from . import document_router
from . import query_router

__all__ = ['document_router', 'query_router']
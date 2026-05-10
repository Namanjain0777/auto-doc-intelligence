"""
PDF Processing Module using pdfplumber
Extracts text, images, and structural information from automotive service manuals
"""

import pdfplumber
import io
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from PIL import Image
import hashlib
import logging

logger = logging.getLogger(__name__)

@dataclass
class TextBlock:
    """Represents a block of text extracted from PDF"""
    content: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_number: int
    block_type: str  # 'text', 'title', 'caption', etc.
    font_info: Dict[str, Any]
    confidence: float = 1.0

@dataclass
class DiagramInfo:
    """Represents an extracted diagram/image from PDF"""
    image_bytes: bytes
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_number: int
    caption: Optional[str] = None
    diagram_id: Optional[str] = None
    confidence: float = 1.0
    mime_type: str = "image/png"

@dataclass
class PDFChunk:
    """Represents a processable chunk of content from PDF"""
    content: str  # Text content or OCR from diagram
    metadata: Dict[str, Any]
    chunk_type: str  # 'text', 'diagram_description', 'table'
    source_info: Dict[str, Any]
    embedding: Optional[List[float]] = None

class AutomotivePDFProcessor:
    """Processes automotive service manual PDFs for multimodal RAG"""
    
    def __init__(self, dpi: int = 300):
        self.dpi = dpi
        
    def extract_content_from_pdf(self, pdf_path: str) -> List[PDFChunk]:
        """
        Extract all content from PDF and return as processable chunks
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of PDFChunk objects containing text and diagram information
        """
        logger.info(f"Processing PDF: {pdf_path}")
        chunks = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                doc_name = pdf_path.split('/')[-1].split('\\')[-1]  # Get filename
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    logger.debug(f"Processing page {page_num + 1}/{total_pages}")
                    
                    # Extract text blocks
                    text_chunks = self._extract_text_blocks(page, page_num, doc_name)
                    chunks.extend(text_chunks)
                    
                    # Extract images/diagrams
                    diagram_chunks = self._extract_diagrams(page, page_num, doc_name)
                    chunks.extend(diagram_chunks)
                    
            logger.info(f"Extracted {len(chunks)} chunks from {pdf_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise
    
    def _extract_text_blocks(self, page: pdfplumber.page.Page, page_num: int, doc_name: str) -> List[PDFChunk]:
        """Extract text blocks from a PDF page"""
        chunks = []
        
        try:
            # Get text with detailed formatting information
            words = page.extract_words()
            
            if not words:
                return chunks
            
            # Group words by their vertical position (lines)
            lines = self._group_words_into_lines(words)
            
            for line_words in lines:
                if not line_words:
                    continue
                
                # Get text from words
                block_text = ' '.join(word['text'] for word in line_words)
                block_text = block_text.strip()
                
                if not block_text:
                    continue
                
                # Get font info from first word of line
                first_word = line_words[0]
                font_size = first_word.get('size', 12)
                font_name = first_word.get('fontname', 'Unknown')
                
                # Get bounding box
                bbox = (
                    first_word['x0'],
                    first_word['top'],
                    line_words[-1]['x1'],
                    line_words[-1]['bottom']
                )
                
                # Determine block type based on formatting
                block_type = self._classify_text_block(font_size, block_text, bbox)
                
                # Create chunk
                chunk = PDFChunk(
                    content=block_text,
                    metadata={
                        "font_size": font_size,
                        "font_name": font_name,
                        "bbox": bbox,
                        "block_type": block_type
                    },
                    chunk_type="text",
                    source_info={
                        "document": doc_name,
                        "page_number": page_num + 1,
                        "extraction_method": "pdfplumber"
                    }
                )
                chunks.append(chunk)
                    
        except Exception as e:
            logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
            
        return chunks
    
    def _group_words_into_lines(self, words: List[Dict[str, Any]], line_threshold: float = 5.0) -> List[List[Dict[str, Any]]]:
        """Group words into lines based on vertical position"""
        if not words:
            return []
        
        # Sort words by top position
        sorted_words = sorted(words, key=lambda w: w['top'])
        
        lines = []
        current_line = [sorted_words[0]]
        current_y = sorted_words[0]['top']
        
        for word in sorted_words[1:]:
            # If word is on a similar vertical position, add to current line
            if abs(word['top'] - current_y) <= line_threshold:
                current_line.append(word)
            else:
                # Start a new line
                lines.append(current_line)
                current_line = [word]
                current_y = word['top']
        
        # Don't forget the last line
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _extract_diagrams(self, page: pdfplumber.page.Page, page_num: int, doc_name: str) -> List[PDFChunk]:
        """Extract diagrams/images from a PDF page"""
        chunks = []
        
        try:
            # Extract images from the page
            images = page.images
            
            for img_index, img_info in enumerate(images):
                try:
                    # Get image data from pdfplumber
                    # Note: pdfplumber extracts image as xobject, we need to get the actual image
                    img_bbox = (
                        img_info.get('x0', 0),
                        img_info.get('top', 0),
                        img_info.get('x1', 0),
                        img_info.get('bottom', 0)
                    )
                    
                    # Try to get the actual image bytes
                    # pdfplumber provides the image stream, but we need to convert it
                    if 'stream' in img_info:
                        # Get image from page's internal objects
                        img_data = self._extract_image_data(page, img_info)
                    else:
                        # Create a placeholder - image extraction from PDF is complex
                        img_data = None
                    
                    # Try to extract caption nearby
                    caption = self._find_caption_near_image(page, img_bbox, page_num)
                    
                    # Generate diagram ID
                    diagram_id = f"FIG_{page_num+1:02d}_{img_index+1:02d}"
                    
                    # Create chunk for diagram (will be processed by vision API later)
                    chunk = PDFChunk(
                        content="",  # Will be filled by vision API
                        metadata={
                            "bbox": list(img_bbox),
                            "image_index": img_index,
                            "image_width": img_info.get('width', 0),
                            "image_height": img_info.get('height', 0),
                        },
                        chunk_type="diagram",
                        source_info={
                            "document": doc_name,
                            "page_number": page_num + 1,
                            "diagram_id": diagram_id,
                            "caption": caption,
                            "extraction_method": "pdfplumber"
                        }
                    )
                    
                    # Store image data if available
                    if img_data:
                        chunk.metadata["image_data"] = img_data
                    
                    chunks.append(chunk)
                    
                except Exception as e:
                    logger.warning(f"Error processing image {img_index} on page {page_num}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error extracting images from page {page_num}: {str(e)}")
            
        return chunks
    
    def _extract_image_data(self, page: pdfplumber.page.Page, img_info: Dict[str, Any]) -> Optional[bytes]:
        """Extract image data from PDF page"""
        try:
            # Try to get the image from the page's objects
            # pdfplumber doesn't directly expose image bytes, so we need a workaround
            # We'll use the page's get_object method if available
            
            # For now, return None and handle in the vision processing
            # In production, you'd use PyMuPDF or pdf2image for this
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract image data: {str(e)}")
            return None
    
    def _classify_text_block(self, font_size: float, text: str, bbox: Tuple[float, float, float, float]) -> str:
        """Classify text block type based on formatting and content"""
        text_lower = text.lower().strip()
        
        # Check for common patterns in automotive manuals
        if any(keyword in text_lower for keyword in ['warning:', 'caution:', 'note:', 'important:']):
            return 'warning'
        elif any(keyword in text_lower for keyword in ['step', 'procedure', 'remove', 'install', 'check']):
            if text_lower.startswith(tuple(str(i) for i in range(1, 10))):  # Starts with number
                return 'procedure_step'
        elif font_size >= 16:
            if any(keyword in text_lower for keyword in ['chapter', 'section']):
                return 'section_header'
            else:
                return 'title'
        elif font_size >= 14:
            return 'subsection_header'
        elif 'table' in text_lower or 'fig.' in text_lower or 'figure' in text_lower:
            return 'caption'
        else:
            return 'body_text'
    
    def _find_caption_near_image(self, page: pdfplumber.page.Page, img_bbox: Tuple, page_num: int) -> Optional[str]:
        """Attempt to find caption text near an image"""
        try:
            x0, y0, x1, y1 = img_bbox
            
            # Expand search area below the image
            search_bottom = y1 + 50
            
            # Extract text in the area below the image
            text = page.extract_text(x0=x0, y0=y1, x1=x1, y1=search_bottom)
            
            if text and len(text.strip()) > 0:
                # Clean up caption
                caption = text.strip()
                # Remove common prefixes
                for prefix in ['Figure', 'Fig.', 'FIGURE', 'Diagram']:
                    if caption.startswith(prefix):
                        caption = caption[len(prefix):].strip(': ')
                        break
                return caption if caption else None
                
        except Exception as e:
            logger.debug(f"Could not find caption for image: {str(e)}")
            
        return None
    
    def process_pdf_bytes(self, pdf_bytes: bytes, filename: str = "uploaded.pdf") -> List[PDFChunk]:
        """
        Process PDF from bytes (useful for API uploads)
        
        Args:
            pdf_bytes: PDF file as bytes
            filename: Name to use for the file
            
        Returns:
            List of PDFChunk objects
        """
        # Save bytes to temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name
        
        try:
            chunks = self.extract_content_from_pdf(tmp_path)
            return chunks
        finally:
            # Clean up temp file
            os.unlink(tmp_path)


if __name__ == "__main__":
    # For testing
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        processor = AutomotivePDFProcessor()
        chunks = processor.extract_content_from_pdf(pdf_path)
        
        print(f"Extracted {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3
            print(f"\nChunk {i+1}:")
            print(f"  Type: {chunk.chunk_type}")
            print(f"  Content: {chunk.content[:100]}...")
            print(f"  Source: {chunk.source_info}")
    else:
        print("Usage: python pdf_processor.py <path_to_pdf>")
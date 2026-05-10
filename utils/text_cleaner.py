"""
Text Cleaning Utilities
Functions for cleaning and preprocessing text extracted from automotive documents
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class TextCleaner:
    """Cleans and preprocesses text extracted from PDFs"""
    
    def __init__(self):
        # Common PDF extraction artifacts to remove
        self.artifacts_patterns = [
            r'\+[\d\s\.\-]+\+',  # Table artifacts like "+-------+"
            r'[\-\_]{3,}',       # Long sequences of dashes or underscores
            r'\s{2,}',           # Multiple consecutive spaces
            r'\[\s*\]',          # Empty brackets
            r'\(\s*\)',          # Empty parentheses
        ]
        
        # Common OCR errors in technical documents
        self.ocr_corrections = {
            r'\b0\b': 'O',       # Zero to O in context (would be smarter in production)
            r'\b1\b': 'I',       # One to I in context
            r'\b5\b': 'S',       # Five to S in context
            r'(?<=[a-z])0(?=[a-z])': 'o',  # Zero between letters to lowercase o
            r'(?<=[A-Z])0(?=[A-Z])': 'O',  # Zero between letters to uppercase O
        }
        
        # Headers/footers patterns to remove (common in PDFs)
        self.header_footer_patterns = [
            r'^Page\s+\d+\s+of\s+\d+',  # "Page 1 of 50"
            r'^\d+\s*$',                 # Just a page number
            r'^Confidential.*$',         # Confidential headers
            r'^.*Propietary.*$',         # Proprietary notices
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text extracted from PDF
        
        Args:
            text: Raw text extracted from PDF
            
        Returns:
            Cleaned text
        """
        if not text or not text.strip():
            return ""
        
        try:
            # Step 1: Basic cleaning
            cleaned = self._remove_artifacts(text)
            
            # Step 2: Fix common OCR errors
            cleaned = self._fix_ocr_errors(cleaned)
            
            # Step 3: Normalize whitespace
            cleaned = self._normalize_whitespace(cleaned)
            
            # Step 4: Remove headers/footers
            cleaned = self._remove_headers_footers(cleaned)
            
            # Step 5: Final trim
            cleaned = cleaned.strip()
            
            logger.debug(f"Cleaned text: {len(text)} -> {len(cleaned)} characters")
            return cleaned
            
        except Exception as e:
            logger.warning(f"Error cleaning text: {str(e)}. Returning original text.")
            return text
    
    def _remove_artifacts(self, text: str) -> str:
        """Remove common PDF extraction artifacts"""
        cleaned = text
        
        for pattern in self.artifacts_patterns:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.MULTILINE)
        
        return cleaned
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors in technical documents"""
        cleaned = text
        
        # Apply OCR corrections carefully
        for pattern, replacement in self.ocr_corrections.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Specific fixes for common automotive OCR errors
        automotive_fixes = {
            r'(?i)rn': 'm',          # "rn" often mistaken for "m"
            r'(?i)vv': 'w',          # "vv" often mistaken for "w"
            r'(?i)cl': 'd',          # "cl" often mistaken for "d" 
            r'(?i)ln': 'li',         # "ln" often mistaken for "li"
            r'¥': 'Y',               # Yen symbol sometimes for Y
            r'€': 'C',               # Euro symbol sometimes for C
            r'§': '5',               # Section symbol sometimes for 5
            r'©': 'C',               # Copyright sometimes for C
            r'®': 'R',               # Registered sometimes for R
        }
        
        for pattern, replacement in automotive_fixes.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters"""
        # Replace various whitespace characters with single space
        cleaned = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks
        cleaned = re.sub(r'\r\n', '\n', cleaned)  # Windows to Unix
        cleaned = re.sub(r'\r', '\n', cleaned)    # Old Mac to Unix
        
        # Remove excessive blank lines
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        return cleaned
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove recurring headers and footers"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                cleaned_lines.append('')
                continue
            
            # Check if line matches header/footer patterns
            is_header_footer = False
            for pattern in self.header_footer_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_header_footer = True
                    break
            
            if not is_header_footer:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_batch(self, texts: List[str]) -> List[str]:
        """Clean a batch of texts"""
        return [self.clean_text(text) for text in texts]


# Convenience functions
def clean_text(text: str) -> str:
    """Convenience function for cleaning a single text string"""
    cleaner = TextCleaner()
    return cleaner.clean_text(text)


def clean_texts(texts: List[str]) -> List[str]:
    """Convenience function for cleaning a list of texts"""
    cleaner = TextCleaner()
    return cleaner.clean_batch(texts)


if __name__ == "__main__":
    # For testing
    import sys
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) > 1:
        # Clean text from file
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
        
        cleaner = TextCleaner()
        cleaned = cleaner.clean_text(text)
        
        print("Original text:")
        print(repr(text[:200]))
        print("\nCleaned text:")
        print(repr(cleaned[:200]))
    else:
        # Test with sample text
        sample_text = """
        Page 1 of 42
        
        BRAKE SYSTEM INSPECTION
        
        1. Check brake pedal height and free play.
           Pedal height should be 195-205 mm from floor panel.
           Pedal free play should be 3-8 mm.
        
        2. Inspect brake lines and hoses for damage or deterioration.
           Look for: cracks, bulges, leaks, or loose fittings.
           
        3. Measure brake pad thickness.
           Minimum thickness: 2.0 mm (0.08 in)
           
        Confidential - Internal Use Only
        00123456789
        """
        
        cleaner = TextCleaner()
        cleaned = cleaner.clean_text(sample_text)
        
        print("Original text:")
        print(repr(sample_text))
        print("\nCleaned text:")
        print(repr(cleaned))
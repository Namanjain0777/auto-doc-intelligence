"""
Gemini Vision API Integration Module
Processes diagrams/images from automotive manuals using Google's Gemini Vision API
"""

import os
import io
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
from PIL import Image
import base64

logger = logging.getLogger(__name__)

@dataclass
class DiagramDescription:
    """Structured description of a diagram from Gemini Vision"""
    description: str
    components: List[str]
    procedures: List[str]
    warnings: List[str]
    specifications: List[str]
    confidence_score: float
    automotive_terms: List[str]
    raw_response: str

class GeminiVisionProcessor:
    """Processes automotive diagrams using Gemini Vision API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Vision processor
        
        Args:
            api_key: Google AI API key. If None, will try to get from environment
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google AI API key is required. Set GOOGLE_API_KEY environment variable.")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Automotive-specific prompt template
        self.automotive_prompt_template = """
        Analyze this automotive technical diagram in detail. Provide a comprehensive description focusing on:
        
        1. Component Identification: Label all visible components with their standard SAE/JASO terminology
        2. Spatial Relationships: Describe how components are connected or related
        3. Functional Pathways: Trace fluid flow, electrical pathways, or mechanical linkages
        4. Diagnostic Indicators: Identify any sensors, warning lights, or test points
        5. Specifications: Note any visible torque values, measurements, or specifications
        6. Procedures: Suggest what maintenance or repair procedure this diagram might illustrate
        7. Warnings: Identify any visible safety warnings or precautions
        
        Format your response as a JSON object with these exact keys:
        - "description": Overall description of the diagram
        - "components": Array of identified component names
        - "procedures": Array of suggested procedures
        - "warnings": Array of safety warnings visible
        - "specifications": Array of numerical specifications or measurements
        - "confidence_score": Your confidence in this analysis (0.0 to 1.0)
        - "automotive_terms": Array of standardized automotive terms used
        
        Be precise and use correct automotive terminology. If uncertain about something, indicate that in your analysis.
        """
    
    def describe_diagram(self, image_bytes: bytes, context_hint: str = "") -> DiagramDescription:
        """
        Analyze a diagram using Gemini Vision API
        
        Args:
            image_bytes: Raw image bytes
            context_hint: Optional context about what the diagram might show
            
        Returns:
            DiagramDescription object with structured analysis
        """
        try:
            # Prepare image for Gemini
            image = Image.open(io.BytesIO(image_bytes))
            
            # Prepare prompt with context if provided
            prompt = self.automotive_prompt_template
            if context_hint:
                prompt += f"\n\nContext hint: This diagram is related to {context_hint}"
            
            # Generate response
            logger.info("Sending diagram to Gemini Vision API")
            response = self.model.generate_content([prompt, image])
            
            # Parse JSON response
            description_obj = self._parse_gemini_response(response.text)
            
            logger.info(f"Received diagram analysis with confidence: {description_obj.confidence_score}")
            return description_obj
            
        except Exception as e:
            logger.error(f"Error processing diagram with Gemini Vision: {str(e)}")
            # Return a fallback description
            return DiagramDescription(
                description=f"Error processing diagram: {str(e)}",
                components=[],
                procedures=[],
                warnings=[],
                specifications=[],
                confidence_score=0.0,
                automotive_terms=[],
                raw_response=str(e)
            )
    
    def _parse_gemini_response(self, response_text: str) -> DiagramDescription:
        """Parse Gemini's response into structured DiagramDescription"""
        try:
            # Try to extract JSON from response
            # Sometimes Gemini wraps JSON in markdown or adds extra text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                response_data = json.loads(json_str)
            else:
                # Fallback: try to parse the whole response as JSON
                response_data = json.loads(response_text)
            
            # Validate and set defaults
            return DiagramDescription(
                description=response_data.get("description", ""),
                components=response_data.get("components", []),
                procedures=response_data.get("procedures", []),
                warnings=response_data.get("warnings", []),
                specifications=response_data.get("specifications", []),
                confidence_score=float(response_data.get("confidence_score", 0.5)),
                automotive_terms=response_data.get("automotive_terms", []),
                raw_response=response_text
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse Gemini response as JSON: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            
            # Fallback: create description from raw text
            return DiagramDescription(
                description=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                components=self._extract_components_from_text(response_text),
                procedures=self._extract_procedures_from_text(response_text),
                warnings=self._extract_warnings_from_text(response_text),
                specifications=self._extract_specifications_from_text(response_text),
                confidence_score=0.3,  # Lower confidence for unparsed response
                automotive_terms=self._extract_automotive_terms(response_text),
                raw_response=response_text
            )
        except Exception as e:
            logger.error(f"Unexpected error parsing Gemini response: {str(e)}")
            return DiagramDescription(
                description="Error parsing Gemini response",
                components=[],
                procedures=[],
                warnings=[],
                specifications=[],
                confidence_score=0.0,
                automotive_terms=[],
                raw_response=response_text
            )
    
    def _extract_components_from_text(self, text: str) -> List[str]:
        """Extract component names from text (simple fallback)"""
        # This would be enhanced with NER in production
        components = []
        # Simple heuristic: look for capitalized terms or known automotive terms
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['sensor', 'valve', 'pump', 'motor', 'module']):
                # Extract potential component name
                words = line.split()
                for i, word in enumerate(words):
                    if any(kw in word.lower() for kw in ['sensor', 'valve', 'pump', 'motor']):
                        if i > 0:
                            components.append(words[i-1] + " " + word)
                        else:
                            components.append(word)
        return list(set(components))[:10]  # Limit and deduplicate
    
    def _extract_procedures_from_text(self, text: str) -> List[str]:
        """Extract procedures from text (simple fallback)"""
        procedures = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['remove', 'install', 'check', 'replace', 'adjust']):
                if len(line.strip()) > 10:  # Reasonable length
                    procedures.append(line.strip())
        return list(set(procedures))[:10]
    
    def _extract_warnings_from_text(self, text: str) -> List[str]:
        """Extract warnings from text (simple fallback)"""
        warnings = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['warning', 'caution', 'danger', 'notice']):
                if len(line.strip()) > 5:
                    warnings.append(line.strip())
        return list(set(warnings))[:10]
    
    def _extract_specifications_from_text(self, text: str) -> List[str]:
        """Extract specifications/numbers from text (simple fallback)"""
        import re
        specs = []
        # Look for patterns like numbers with units
        patterns = [
            r'\d+\s*(?:Nm|ft-lb|psi|bar|mm|in|°C|°F|volts?|amps?|ohms?)',
            r'Torque:\s*\d+',
            r'Pressure:\s*\d+',
            r'Voltage:\s*\d+'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            specs.extend(matches)
        
        return list(set(specs))[:10]
    
    def _extract_automotive_terms(self, text: str) -> List[str]:
        """Extract standardized automotive terms from text"""
        # Common automotive terms - in production would use ontology
        auto_terms = [
            'ABS', 'ECU', 'ECM', 'PCM', 'TCM', 'BCM',
            'MIL', 'DTC', 'OBD', 'CAN', 'LIN',
            'TPS', 'MAP', 'MAF', 'O2', 'EGR',
            'PCV', 'EVAP', 'VVT', 'VTEC', 'TDC',
            'BDC', 'RPM', 'MPG', 'HP', 'Torque'
        ]
        
        found_terms = []
        text_upper = text.upper()
        for term in auto_terms:
            if term in text_upper:
                found_terms.append(term)
        
        return list(set(found_terms))
    
    def batch_describe_diagrams(self, diagram_data_list: List[tuple]) -> List[DiagramDescription]:
        """
        Process multiple diagrams in batch
        
        Args:
            diagram_data_list: List of (image_data, context_hint) tuples
            
        Returns:
            List of DiagramDescription objects
        """
        results = []
        for i, (image_data, context_hint) in enumerate(diagram_data_list):
            logger.info(f"Processing diagram {i+1}/{len(diagram_data_list)}")
            description = self.describe_diagram(image_data, context_hint)
            results.append(description)
        return results


# Utility functions for direct usage
def describe_diagram_from_path(image_path: str, api_key: Optional[str] = None, context_hint: str = "") -> DiagramDescription:
    """
    Convenience function to describe a diagram from file path
    
    Args:
        image_path: Path to image file
        api_key: Google AI API key
        context_hint: Optional context about the diagram
        
    Returns:
        DiagramDescription object
    """
    processor = GeminiVisionProcessor(api_key)
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    return processor.describe_diagram(image_data, context_hint)


if __name__ == "__main__":
    # For testing
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        context = sys.argv[2] if len(sys.argv) > 2 else ""
        
        try:
            description = describe_diagram_from_path(image_path, context_hint=context)
            print(json.dumps(asdict(description), indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    else:
        print("Usage: python gemini_processor.py <image_path> [context_hint]")
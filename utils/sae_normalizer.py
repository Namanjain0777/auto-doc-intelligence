"""
SAE Terminology Normalizer
Functions for normalizing automotive terminology to SAE/JASO standards
"""

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class SAENormalizer:
    """Normalizes automotive terminology to SAE/JASO standards"""
    
    def __init__(self):
        # SAE/JASO standard term mappings
        # Common colloquial terms -> Standard SAE terms
        self.term_mappings = {
            # Engine components
            "check engine light": "malfunction indicator lamp (mil)",
            "cel": "malfunction indicator lamp (mil)",
            "engine light": "malfunction indicator lamp (mil)",
            "motor": "engine",
            "spark plugs": "spark plugs",
            "plugs": "spark plugs",
            "fuel injector": "fuel injector",
            "injectors": "fuel injectors",
            "air filter": "air cleaner element",
            "oil filter": "lubricating oil filter",
            "timing belt": "timing belt",
            "timing chain": "timing chain",
            "camshaft": "camshaft",
            "crankshaft": "crankshaft",
            "piston": "piston",
            "connecting rod": "connecting rod",
            "valve": "valve",
            "intake valve": "intake valve",
            "exhaust valve": "exhaust valve",
            
            # Transmission
            "transmission": "transmission",
            "transaxle": "transaxle",
            "clutch": "clutch",
            "torque converter": "torque converter",
            "gearbox": "transmission",
            "shift lever": "gearshift lever",
            "gear selector": "gearshift lever",
            
            # Brakes
            "brake pads": "brake lining",
            "brake shoes": "brake lining",
            "brake rotors": "brake disc",
            "brake drums": "brake drum",
            "brake fluid": "hydraulic brake fluid",
            "abs": "antilock brake system (abs)",
            "esc": "electronic stability control (esc)",
            "traction control": "traction control system (tcs)",
            
            # Electrical
            "battery": "storage battery",
            "alternator": "generator",
            "starter": "cranking motor",
            "spark plug wires": "secondary ignition wiring",
            "distributor": "distributor",
            "ignition coil": "ignition coil",
            "fuses": "fuses",
            "relay": "relay",
            "wiring harness": "wiring harness",
            
            # Cooling
            "radiator": "radiator",
            "coolant": "engine coolant",
            "antifreeze": "engine coolant",
            "water pump": "coolant pump",
            "thermostat": "cooling system thermostat",
            "cooling fan": "radiator cooling fan",
            
            # Fuel
            "fuel pump": "fuel pump",
            "fuel tank": "fuel tank",
            "fuel lines": "fuel lines",
            "carburetor": "carburetor",
            "throttle body": "throttle body",
            "intake manifold": "intake manifold",
            "exhaust manifold": "exhaust manifold",
            "catalytic converter": "catalytic converter",
            "muffler": "muffler",
            "oxygen sensor": "oxygen sensor",
            "o2 sensor": "oxygen sensor",
            
            # Suspension/Steering
            "shocks": "shock absorbers",
            "struts": "strut assemblies",
            "springs": "suspension springs",
            "control arms": "control arms",
            "ball joints": "ball joints",
            "tie rods": "tie rod ends",
            "steering rack": "steering gear",
            "power steering": "power steering system",
            
            # Tires/Wheels
            "tires": "tires",
            "wheels": "wheels",
            "lug nuts": "wheel lug nuts",
            "hub": "wheel hub",
            "bearing": "wheel bearing",
            
            # HVAC
            "ac": "air conditioning system",
            "heater": "heating system",
            "blower": "blower motor",
            "compressor": "compressor",
            "condenser": "condenser",
            "evaporator": "evaporator",
            
            # General maintenance terms
            "service": "maintenance",
            "fix": "repair",
            "change": "replace",
            "check": "inspect",
            "look at": "examine",
            "see if": "determine",
        }
        
        # Units and measurements standardization
        self.unit_mappings = {
            # Pressure
            r'\bbi\b': 'psi',
            r'\bpounds per square inch\b': 'psi',
            r'\bkilo\s*pascal\b': 'kPa',
            r'\bkilopascal\b': 'kPa',
            r'\bbar\b': 'bar',
            
            # Torque
            r'\bbi\b': 'lb-ft',
            r'\bpound-feet\b': 'lb-ft',
            r'\bpound\s*feet\b': 'lb-ft',
            r'\bnewton\s*meter\b': 'N·m',
            r'\bnewton\s*metre\b': 'N·m',
            r'\bnm\b': 'N·m',
            r'\bkgf\s*cm\b': 'kgf·cm',
            r'\bkilogram-force\s*centimeter\b': 'kgf·cm',
            
            # Length/Distance
            r'\binch\b': 'in',
            r'\binches\b': 'in',
            r'\b\"\b': 'in',
            r'\bfoot\b': 'ft',
            r'\bfeet\b': 'ft',
            r"\b'\b": 'ft',
            r'\bmillimeter\b': 'mm',
            r'\bmillimetres\b': 'mm',
            r'\bmm\b': 'mm',
            r'\bcentimeter\b': 'cm',
            r'\bcentimetres\b': 'cm',
            r'\bcm\b': 'cm',
            r'\bmeter\b': 'm',
            r'\bmetre\b': 'm',
            r'\bm\b': 'm',
            r'\bkilometer\b': 'km',
            r'\bkilometre\b': 'km',
            r'\bkm\b': 'km',
            
            # Volume
            r'\bquart\b': 'qt',
            r'\bquarts\b': 'qt',
            r'\bpint\b': 'pt',
            r'\bpints\b': 'pt',
            r'\bgallon\b': 'gal',
            r'\bgallons\b': 'gal',
            r'\bliter\b': 'L',
            r'\blitre\b': 'L',
            r'\bml\b': 'mL',
            r'\bmilliliter\b': 'mL',
            r'\bmillilitre\b': 'mL',
            
            # Weight/Mass
            r'\bpound\b': 'lb',
            r'\bpounds\b': 'lb',
            r'\blbs\b': 'lb',
            r'\bkilogram\b': 'kg',
            r'\bkilograms\b': 'kg',
            r'\bkg\b': 'kg',
            r'\bounce\b': 'oz',
            r'\bounces\b': 'oz',
            
            # Temperature
            r'\bdegree\s*fahrenheit\b': '°F',
            r'\bdegrees\s*fahrenheit\b': '°F',
            r'\b°f\b': '°F',
            r'\bfahrenheit\b': '°F',
            r'\bdegree\s*celsius\b': '°C',
            r'\bdegrees\s*celsius\b': '°C',
            r'\b°c\b': '°C',
            r'\bcelsius\b': '°C',
            r'\bkelvin\b': 'K',
            
            # Electrical
            r'\bvolt\b': 'V',
            r'\bvolts\b': 'V',
            r'\bkv\b': 'kV',
            r'\bkilovolt\b': 'kV',
            r'\bamp\b': 'A',
            r'\bamps\b': 'A',
            r'\bampere\b': 'A',
            r'\bamperes\b': 'A',
            r'\bma\b': 'mA',
            r'\bmilliamp\b': 'mA',
            r'\bmilliampere\b': 'mA',
            r'\bomega\b': 'Ω',
            r'\bohm\b': 'Ω',
            r'\bohms\b': 'Ω',
            r'\bkw\b': 'kW',
            r'\bkilowatt\b': 'kW',
            r'\bhp\b': 'hp',
            r'\bhorsepower\b': 'hp',
        }
        
        # Compile regex patterns for efficiency
        self.term_patterns = {re.compile(re.escape(k), re.IGNORECASE): v 
                             for k, v in self.term_mappings.items()}
        self.unit_patterns = [(re.compile(pattern, re.IGNORECASE), replacement) 
                             for pattern, replacement in self.unit_mappings.items()]
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize automotive terminology in text to SAE/JASO standards
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text with standard terminology
        """
        if not text or not text.strip():
            return text
        
        try:
            normalized = text
            
            # Apply term mappings
            normalized = self._apply_term_mappings(normalized)
            
            # Apply unit mappings
            normalized = self._apply_unit_mappings(normalized)
            
            # Fix spacing and punctuation
            normalized = self._fix_spacing(normalized)
            
            logger.debug(f"Normalized text: {len(text)} -> {len(normalized)} characters")
            return normalized
            
        except Exception as e:
            logger.warning(f"Error normalizing text: {str(e)}. Returning original text.")
            return text
    
    def _apply_term_mappings(self, text: str) -> str:
        """Apply terminology mappings to text"""
        normalized = text
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_patterns = sorted(self.term_patterns.items(), 
                               key=lambda x: len(x[0].pattern), 
                               reverse=True)
        
        for pattern, replacement in sorted_patterns:
            # Use word boundaries to avoid partial replacements
            def replace_match(match):
                # Preserve original case pattern
                matched_text = match.group(0)
                if matched_text.islower():
                    return replacement.lower()
                elif matched_text.isupper():
                    return replacement.upper()
                elif matched_text[0].isupper():
                    # Capitalized - capitalize first letter of replacement
                    if replacement:
                        return replacement[0].upper() + replacement[1:].lower()
                    else:
                        return replacement
                else:
                    return replacement
            
            normalized = pattern.sub(replace_match, normalized)
        
        return normalized
    
    def _apply_unit_mappings(self, text: str) -> str:
        """Apply unit mappings to text"""
        normalized = text
        
        for pattern, replacement in self.unit_patterns:
            normalized = pattern.sub(replacement, normalized)
        
        return normalized
    
    def _fix_spacing(self, text: str) -> str:
        """Fix spacing issues after normalization"""
        # Fix spacing around slashes and hyphens in compound terms
        text = re.sub(r'\s*/\s*', '/', text)
        text = re.sub(r'\s*-\s*', '-', text)
        text = re.sub(r'\s*·\s*', '·', text)  # Middle dot for N·m
        
        # Fix multiple spaces
        text = re.sub(r'\s{2,}', ' ', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s*([,.!?:;])\s*', r'\1 ', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def normalize_terms_list(self, terms: List[str]) -> List[str]:
        """
        Normalize a list of terms (e.g., extracted components)
        
        Args:
            terms: List of terminology strings
            
        Returns:
            List of normalized terms
        """
        return [self.normalize_text(term) for term in terms if term.strip()]
    
    def get_standard_term(self, term: str) -> str:
        """
        Get the standard SAE term for a given term
        
        Args:
            term: Input term to look up
            
        Returns:
            Standardized term or original if no mapping found
        """
        term_lower = term.lower().strip()
        return self.term_mappings.get(term_lower, term)
    
    def add_custom_mapping(self, colloquial: str, standard: str):
        """
        Add a custom term mapping
        
        Args:
            colloquial: Colloquial or variant term
            standard: Standard SAE/JASO term
        """
        self.term_mappings[colloquial.lower()] = standard
        # Rebuild patterns
        self.term_patterns = {re.compile(re.escape(k), re.IGNORECASE): v 
                             for k, v in self.term_mappings.items()}
        # Resort by length
        sorted_items = sorted(self.term_patterns.items(), 
                            key=lambda x: len(x[0].pattern), 
                            reverse=True)
        self.term_patterns = dict(sorted_items)
        
        logger.info(f"Added custom mapping: '{colloquial}' -> '{standard}'")
    
    def load_mappings_from_file(self, filepath: str):
        """
        Load term mappings from a JSON file
        
        Args:
            filepath: Path to JSON file containing mappings
        """
        try:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            
            for colloquial, standard in mappings.items():
                self.add_custom_mapping(colloquial, standard)
                
            logger.info(f"Loaded {len(mappings)} term mappings from {filepath}")
        except Exception as e:
            logger.error(f"Error loading mappings from {filepath}: {str(e)}")


# Convenience functions
def normalize_text(text: str) -> str:
    """Convenience function for normalizing a single text string"""
    normalizer = SAENormalizer()
    return normalizer.normalize_text(text)


def normalize_terms(terms: List[str]) -> List[str]:
    """Convenience function for normalizing a list of terms"""
    normalizer = SAENormalizer()
    return normalizer.normalize_terms_list(terms)


def get_standard_term(term: str) -> str:
    """Convenience function to get standard term for a single term"""
    normalizer = SAENormalizer()
    return normalizer.get_standard_term(term)


if __name__ == "__main__":
    # For testing
    import sys
    import json
    logging.basicConfig(level=logging.DEBUG)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Run built-in tests
            normalizer = SAENormalizer()
            
            test_cases = [
                "Check the engine light for codes",
                "Replace the brake pads and rotors",
                "Check torque specs: 80 lb-ft",
                "The coolant level is low in the radiator",
                "Check fuel pressure: 45 psi",
                "Replace the spark plugs and wires",
                "The ABS light is on",
                "Check the tire pressure: 32 psi",
                "Change the oil and filter",
                "Inspect the timing belt for wear"
            ]
            
            print("SAE Terminology Normalization Tests:")
            print("=" * 50)
            for test in test_cases:
                normalized = normalizer.normalize_text(test)
                print(f"Original:  {test}")
                print(f"Normalized: {normalized}")
                print()
        elif sys.argv[1] == "--file" and len(sys.argv) > 2:
            # Load mappings from file
            normalizer = SAENormalizer()
            normalizer.load_mappings_from_file(sys.argv[2])
            print(f"Loaded mappings from {sys.argv[2]}")
        else:
            # Normalize text from command line
            text = " ".join(sys.argv[1:])
            normalized = normalize_text(text)
            print(f"Original: {text}")
            print(f"Normalized: {normalized}")
    else:
        # Demo with sample text
        sample_texts = [
            "Check engine light is on, need to check codes",
            "Replace brake pads and rotors, torque lug nuts to 80 ft-lb",
            "Coolant low in radiator, check for leaks",
            "Fuel pressure at 45 psi, replace fuel filter",
            "Timing belt shows wear, replace at 90k miles",
            "Tire pressure 32 psi front, 35 psi rear",
            "Oil change needed, use 5W-30 synthetic",
            "Battery voltage 12.6V, alternator charging at 14.2V"
        ]
        
        print("SAE Terminology Normalizer Demo:")
        print("=" * 40)
        for text in sample_texts:
            normalized = normalize_text(text)
            print(f"Input:  {text}")
            print(f"Output: {normalized}")
            print()
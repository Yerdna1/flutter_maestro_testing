"""
UI Element Matcher - matches text descriptions to detected UI elements
"""
import re
import logging
from typing import List, Optional, Tuple
from fuzzywuzzy import fuzz, process
from dataclasses import dataclass

from src.vision import UIElement

logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Result of matching a text description to a UI element"""
    element: UIElement
    score: float
    match_type: str  # 'exact', 'fuzzy', 'partial'

class UIElementMatcher:
    """Matches test case descriptions to detected UI elements"""
    
    def __init__(self, fuzzy_threshold: float = 70.0):
        self.fuzzy_threshold = fuzzy_threshold
        
        # Common UI element synonyms
        self.synonyms = {
            'button': ['btn', 'button', 'submit', 'click'],
            'field': ['field', 'input', 'textbox', 'text field', 'entry'],
            'link': ['link', 'href', 'hyperlink'],
            'image': ['img', 'image', 'picture', 'photo'],
            'icon': ['icon', 'ico'],
            'menu': ['menu', 'dropdown', 'select'],
            'checkbox': ['checkbox', 'check', 'tick'],
            'radio': ['radio', 'option'],
            'tab': ['tab', 'page'],
        }
        
        # Element type keywords
        self.element_types = {
            'button': ['button', 'btn', 'submit', 'prihlasit', 'login', 'sign in'],
            'input': ['field', 'input', 'text', 'password', 'email', 'username'],
            'link': ['link', 'href'],
        }
        
        # Slovak character OCR error mappings for common misreadings
        self.slovak_ocr_fixes = {
            'iekara': 'lekara',  # I misread as L
            'vyhiadat': 'vyhladat',  # l misread as i
            'Iekara': 'Lekara',
            'vyhIadat': 'vyhladat',  # L misread as I (uppercase)
            'zadajte': 'zadajte',  # Common variations
            'rc/id': 'rc/id',
        }
    
    def _normalize_slovak_text(self, text: str) -> str:
        """Normalize Slovak text by fixing common OCR errors"""
        normalized = text.lower()
        for ocr_error, correct in self.slovak_ocr_fixes.items():
            normalized = normalized.replace(ocr_error.lower(), correct.lower())
        return normalized
    
    def find_best_match(self, target_description: str, elements: List[UIElement]) -> Optional[MatchResult]:
        """
        Find the best matching UI element for a target description
        
        Args:
            target_description: Text description from test case
            elements: List of detected UI elements
            
        Returns:
            Best matching element or None if no good match found
        """
        if not elements:
            return None
        
        target_description = target_description.lower().strip()
        # Normalize Slovak text to handle OCR errors
        normalized_target = self._normalize_slovak_text(target_description)
        best_match = None
        best_score = 0.0
        
        # Try exact matching first (with Slovak normalization)
        for element in elements:
            element_desc = element.description.lower()
            element_ocr = element.ocr_text.lower() if element.ocr_text else ""
            # Also normalize the element text for comparison
            normalized_element_desc = self._normalize_slovak_text(element_desc)
            normalized_element_ocr = self._normalize_slovak_text(element_ocr)
            
            # Check for exact match using normalized text (both description and OCR)
            # Only check if strings are non-empty to avoid false matches with empty strings
            desc_match = (normalized_target in normalized_element_desc or 
                         normalized_element_desc in normalized_target or
                         target_description in element_desc or 
                         element_desc in target_description) and element_desc.strip()
            
            ocr_match = (normalized_target in normalized_element_ocr or 
                        normalized_element_ocr in normalized_target or
                        target_description in element_ocr or 
                        element_ocr in target_description) and element_ocr.strip()
            
            if desc_match or ocr_match:
                score = 100.0
                if score > best_score:
                    best_score = score
                    best_match = MatchResult(element, score, 'exact')
        
        # If no exact match, try fuzzy matching (with Slovak normalization)
        if not best_match:
            # Prepare element descriptions and OCR text for fuzzy matching
            element_data = []
            for e in elements:
                element_desc = e.description.lower()
                element_ocr = e.ocr_text.lower() if e.ocr_text else ""
                normalized_desc = self._normalize_slovak_text(element_desc)
                normalized_ocr = self._normalize_slovak_text(element_ocr)
                element_data.append((e, element_desc, normalized_desc, element_ocr, normalized_ocr))
            
            # Use fuzzy matching
            for element, element_desc, normalized_element_desc, element_ocr, normalized_element_ocr in element_data:
                # Try different fuzzy matching strategies on both description and OCR text
                scores = [
                    # Description matching
                    fuzz.ratio(target_description, element_desc),
                    fuzz.partial_ratio(target_description, element_desc),
                    fuzz.token_sort_ratio(target_description, element_desc),
                    fuzz.token_set_ratio(target_description, element_desc),
                    fuzz.ratio(normalized_target, normalized_element_desc),
                    # OCR text matching
                    fuzz.ratio(target_description, element_ocr),
                    fuzz.partial_ratio(target_description, element_ocr),
                    fuzz.token_sort_ratio(target_description, element_ocr),
                    fuzz.token_set_ratio(target_description, element_ocr),
                    fuzz.ratio(normalized_target, normalized_element_ocr),
                    fuzz.partial_ratio(normalized_target, normalized_element_desc),
                    fuzz.token_sort_ratio(normalized_target, normalized_element_desc),
                    fuzz.token_set_ratio(normalized_target, normalized_element_desc),
                ]
                
                max_score = max(scores)
                
                # Check if target contains element type keywords
                type_boost = self._get_type_match_boost(target_description, element_desc)
                max_score = min(100, max_score + type_boost)
                
                if max_score > best_score and max_score >= self.fuzzy_threshold:
                    best_score = max_score
                    best_match = MatchResult(element, max_score, 'fuzzy')
        
        # If still no match, try partial keyword matching
        if not best_match:
            best_match = self._partial_keyword_match(target_description, elements)
        
        if best_match:
            logger.info(f"Matched '{target_description}' to '{best_match.element.description}' "
                       f"(score: {best_match.score:.1f}, type: {best_match.match_type})")
        else:
            logger.warning(f"No match found for '{target_description}'")
        
        # Try specialized Slovak login form matching if no match found
        if not best_match:
            best_match = self._slovak_login_form_match(target_description, elements)
        
        return best_match
    
    def _slovak_login_form_match(self, target: str, elements: List[UIElement]) -> Optional[MatchResult]:
        """Specialized matching for Slovak login forms based on position and element type"""
        target_lower = target.lower()
        
        # Sort elements by Y position (top to bottom)
        sorted_elements = sorted(elements, key=lambda e: (e.bbox[1] + e.bbox[3]) / 2)
        
        # Find input fields and buttons based on position and type
        # Login form elements are typically in the top-middle area
        input_fields = [e for e in sorted_elements if e.element_type in ['text_input', 'text_field', 'banner'] 
                       and 300 < e.bbox[1] < 600 and 2200 < e.bbox[0] < 2900]  # Specific to Unilabs login form
        buttons = [e for e in sorted_elements if e.element_type in ['button', 'banner', 'text_field'] 
                  and 600 < e.bbox[1] < 800 and 2200 < e.bbox[0] < 2900]  # Login button area
        
        logger.info(f"Slovak matching for '{target}': found {len(input_fields)} inputs, {len(buttons)} buttons")
        
        # Match based on Slovak UI patterns
        if any(word in target_lower for word in ['prihlasovacie', 'meno', 'email', 'login', 'username']):
            # First input field (email/username) - usually top field
            if input_fields:
                return MatchResult(input_fields[0], 90.0, 'slovak_position')
                
        elif any(word in target_lower for word in ['heslo', 'password']):
            # Second input field (password) - usually middle field  
            if len(input_fields) >= 2:
                return MatchResult(input_fields[1], 90.0, 'slovak_position')
                
        elif any(word in target_lower for word in ['prihlasit', 'login', 'submit']):
            # Login button - usually below input fields
            if buttons:
                return MatchResult(buttons[0], 90.0, 'slovak_position')
                
        elif any(word in target_lower for word in ['vyhľadať', 'search', 'lekara', 'doctor']):
            # Search field - only match if we're NOT on login page
            # Login page has "Heslo" and "Prihlasovacie meno" elements
            login_indicators = [e for e in elements if e.ocr_text and 
                              ('heslo' in e.ocr_text.lower() or 'prihlasovacie' in e.ocr_text.lower())]
            
            if login_indicators:
                logger.warning(f"Skipping search field match - appears to be on login page")
                return None  # Don't match search fields on login page
                
            # Search field - usually at the top of the page (header area)
            # Updated Y-coordinate range to match actual Unilabs layout
            search_inputs = [e for e in elements if e.element_type in ['text_input', 'text_field', 'phone_number'] 
                             and 100 < e.bbox[1] < 400 and 50 < e.bbox[0] < 1000  # Top area, left side
                             # Exclude fields that have specific non-search OCR text
                             and not (e.ocr_text and (
                                 any(exclude in e.ocr_text.lower() 
                                     for exclude in ['rc/id', 'zadajte', 'datum', 'dátum', 'date'])
                                 or re.match(r'^\d+\.\s*\d+.*\d{4}', e.ocr_text.strip())  # Date pattern
                                 or '2025' in e.ocr_text  # Year in date
                             ))]
            
            logger.info(f"Slovak search field matching: found {len(search_inputs)} potential inputs after filtering")
            for i, e in enumerate(search_inputs[:3]):
                logger.debug(f"  Candidate {i+1}: Type={e.element_type}, OCR='{e.ocr_text}', Y={e.bbox[1]:.0f}")
            
            if search_inputs:
                # Sort by Y coordinate first (prefer higher fields), then by X coordinate
                search_inputs.sort(key=lambda e: (e.bbox[1], e.bbox[0]))
                logger.info(f"Selected search field: Type={search_inputs[0].element_type}, OCR='{search_inputs[0].ocr_text}', Pos={search_inputs[0].bbox}")
                return MatchResult(search_inputs[0], 85.0, 'slovak_search')
            else:
                logger.warning("No suitable search field found - may need to adjust position criteria")
                
        elif any(word in target_lower for word in ['zadajte', 'rc', 'id', 'patient']):
            # Patient ID field - only match if we're NOT on login page
            login_indicators = [e for e in elements if e.ocr_text and 
                              ('heslo' in e.ocr_text.lower() or 'prihlasovacie' in e.ocr_text.lower())]
            
            if login_indicators:
                logger.warning(f"Skipping patient ID match - appears to be on login page")
                return None
                
            # First check if we can find by OCR text
            for e in elements:
                if e.ocr_text and 'rc/id' in e.ocr_text.lower():
                    # Found the label, now find the associated input field
                    # Input fields are usually to the right or below the label
                    label_center_x = (e.bbox[0] + e.bbox[2]) / 2
                    label_center_y = (e.bbox[1] + e.bbox[3]) / 2
                    
                    # Look for input fields near this label
                    nearby_inputs = [el for el in elements if el.element_type in ['text_input', 'text_field', 'phone_number']
                                    and abs((el.bbox[1] + el.bbox[3]) / 2 - label_center_y) < 100  # Same row
                                    and el.bbox[0] > label_center_x]  # To the right
                    
                    if nearby_inputs:
                        # Sort by distance and take the closest
                        nearby_inputs.sort(key=lambda el: el.bbox[0])
                        return MatchResult(nearby_inputs[0], 90.0, 'slovak_patient')
            
            # Fallback: Patient ID field - usually in the top area, after search field
            patient_inputs = [e for e in elements if e.element_type in ['text_input', 'text_field', 'phone_number'] 
                             and 100 < e.bbox[1] < 400 and e.bbox[0] > 300]  # Top area, not leftmost
            if patient_inputs:
                # Sort by X coordinate to avoid the search field
                patient_inputs.sort(key=lambda e: e.bbox[0])
                if len(patient_inputs) > 1:
                    # Skip the first one if it might be the search field
                    return MatchResult(patient_inputs[1], 85.0, 'slovak_patient')
                elif patient_inputs:
                    return MatchResult(patient_inputs[0], 85.0, 'slovak_patient')
                
        elif any(word in target_lower for word in ['nová', 'objednávka', 'new', 'order']):
            # New order button - only match if we're NOT on login page
            login_indicators = [e for e in elements if e.ocr_text and 
                              ('heslo' in e.ocr_text.lower() or 'prihlasovacie' in e.ocr_text.lower())]
            
            if login_indicators:
                logger.warning(f"Skipping new order match - appears to be on login page")
                return None
                
            # First check if we can find by OCR text
            for e in elements:
                if e.ocr_text and ('nova' in e.ocr_text.lower() or 'objednav' in e.ocr_text.lower()):
                    return MatchResult(e, 95.0, 'slovak_new_order')
                    
            # New order button - usually in the top right area
            order_buttons = [e for e in elements if e.element_type in ['button', 'banner', 'label'] 
                            and 100 < e.bbox[1] < 500 and e.bbox[0] > 1500]  # Top area, right side
            if order_buttons:
                return MatchResult(order_buttons[0], 85.0, 'slovak_new_order')
                
        elif any(word in target_lower for word in ['biochémia', 'klinická', 'category', 'test']):
            # Category selection - only match if we're NOT on login page
            login_indicators = [e for e in elements if e.ocr_text and 
                              ('heslo' in e.ocr_text.lower() or 'prihlasovacie' in e.ocr_text.lower())]
            
            if login_indicators:
                logger.warning(f"Skipping category match - appears to be on login page")
                return None
                
            # Category selection - usually in lower content area
            category_elements = [e for e in elements if e.element_type in ['button', 'banner', 'container'] and e.bbox[1] > 1000]
            if category_elements:
                return MatchResult(category_elements[0], 85.0, 'slovak_category')
        
        return None
    
    def _get_type_match_boost(self, target: str, element_desc: str) -> float:
        """Get boost score if target and element share element type keywords"""
        boost = 0.0
        
        for element_type, keywords in self.element_types.items():
            target_has_type = any(kw in target for kw in keywords)
            element_has_type = any(kw in element_desc for kw in keywords)
            
            if target_has_type and element_has_type:
                boost = 10.0
                break
        
        return boost
    
    def _partial_keyword_match(self, target: str, elements: List[UIElement]) -> Optional[MatchResult]:
        """Try matching based on partial keywords"""
        # Extract important keywords from target
        keywords = self._extract_keywords(target)
        
        if not keywords:
            return None
        
        best_match = None
        best_score = 0.0
        
        for element in elements:
            element_desc = element.description.lower()
            matching_keywords = sum(1 for kw in keywords if kw in element_desc)
            
            if matching_keywords > 0:
                score = (matching_keywords / len(keywords)) * 80  # Max 80 for partial match
                if score > best_score and score >= 50:  # Lower threshold for partial
                    best_score = score
                    best_match = MatchResult(element, score, 'partial')
        
        return best_match
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'find'}
        
        # Split and filter
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def match_multiple(self, target: str, elements: List[UIElement], max_matches: int = 3) -> List[MatchResult]:
        """Find multiple matching elements, sorted by score"""
        matches = []
        
        for element in elements:
            # Try to match this element
            element_desc = element.description.lower()
            
            # Calculate match score
            scores = [
                fuzz.ratio(target.lower(), element_desc),
                fuzz.partial_ratio(target.lower(), element_desc),
            ]
            max_score = max(scores)
            
            if max_score >= self.fuzzy_threshold:
                match_type = 'exact' if max_score == 100 else 'fuzzy'
                matches.append(MatchResult(element, max_score, match_type))
        
        # Sort by score descending and return top matches
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:max_matches]
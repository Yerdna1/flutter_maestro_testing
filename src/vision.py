"""
OmniParser integration for UI element detection
"""
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import torch
from PIL import Image
import numpy as np
import cv2
import easyocr

# Add OmniParser to path if needed
OMNIPARSER_PATH = Path(__file__).parent.parent / "OmniParser"
if OMNIPARSER_PATH.exists():
    sys.path.insert(0, str(OMNIPARSER_PATH))

logger = logging.getLogger(__name__)

@dataclass
class UIElement:
    """Represents a detected UI element"""
    bbox: List[float]  # [x1, y1, x2, y2]
    description: str
    confidence: float
    element_type: str = "interactive"
    ocr_text: str = ""  # Text extracted from OCR

class OmniParserVision:
    """OmniParser integration for UI element detection"""
    
    def __init__(self, weights_dir: str = "weights", skip_captioning: bool = True):
        self.weights_dir = Path(weights_dir)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.yolo_model = None
        self.caption_model_processor = None
        self.ocr_reader = None
        self.skip_captioning = skip_captioning
        self._load_models()
    
    def _load_models(self):
        """Load OmniParser models"""
        try:
            # Import OmniParser utilities
            from util.utils_simplified import get_yolo_model, get_caption_model_processor
            
            # Load YOLO model for element detection
            yolo_path = self.weights_dir / "icon_detect" / "model.pt"
            if not yolo_path.exists():
                raise FileNotFoundError(f"YOLO model not found at {yolo_path}")
            
            logger.info(f"Loading YOLO model from {yolo_path}")
            self.yolo_model = get_yolo_model(str(yolo_path))
            
            # Load Florence-2 model for element captioning (if not skipping)
            if not self.skip_captioning:
                florence_path = self.weights_dir / "icon_caption_florence"
                if not florence_path.exists():
                    raise FileNotFoundError(f"Florence model not found at {florence_path}")
                
                logger.info(f"Loading Florence-2 model from {florence_path}")
                self.caption_model_processor = get_caption_model_processor(
                    model_name="florence2", 
                    model_name_or_path=str(florence_path),
                    device=self.device
                )
            
            # Initialize OCR reader
            logger.info("Loading OCR reader...")
            self.ocr_reader = easyocr.Reader(['en'])
            
            logger.info("Models loaded successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import required libraries: {e}")
            logger.error("Please ensure ultralytics and transformers are installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def detect_elements(self, image_path: str) -> List[UIElement]:
        """
        Detect UI elements in an image
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            List of detected UI elements with bounding boxes and descriptions
        """
        if not self.yolo_model:
            raise RuntimeError("YOLO model not loaded. Call _load_models() first.")
        if not self.skip_captioning and not self.caption_model_processor:
            raise RuntimeError("Caption model not loaded. Call _load_models() first.")
        
        # Load image
        image = Image.open(image_path)
        image_np = np.array(image)
        
        # Detect interactive elements
        logger.info(f"Detecting elements in {image_path}")
        results = self.yolo_model(image_np, imgsz=640, conf=0.2, iou=0.9)
        
        elements = []
        
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            
            # Get boxes in normalized format
            normalized_boxes = []
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                confidence = box.conf[0].cpu().item()
                
                # Convert to normalized coordinates [x1, y1, x2, y2]
                h, w = image_np.shape[:2]
                x1, y1, x2, y2 = xyxy[0]/w, xyxy[1]/h, xyxy[2]/w, xyxy[3]/h
                normalized_boxes.append([x1, y1, x2, y2, confidence])
            
            # Generate captions for detected elements (or use simple labels)
            if normalized_boxes:
                if self.skip_captioning:
                    # Fast path: just use simple labels
                    for i, box in enumerate(normalized_boxes):
                        x1, y1, x2, y2, confidence = box
                        
                        # Convert back to pixel coordinates
                        h, w = image_np.shape[:2]
                        pixel_x1, pixel_y1 = x1 * w, y1 * h
                        pixel_x2, pixel_y2 = x2 * w, y2 * h
                        
                        element = UIElement(
                            bbox=[float(pixel_x1), float(pixel_y1), float(pixel_x2), float(pixel_y2)],
                            description=f"UI Element {i+1}",
                            confidence=float(confidence)
                        )
                        elements.append(element)
                else:
                    # Slow path: generate captions using Florence-2
                    from util.utils_simplified import get_parsed_content_icon
                    
                    try:
                        parsed_content = get_parsed_content_icon(
                            filtered_boxes=normalized_boxes,
                            starting_idx=0,
                            image_source=image_np,
                            caption_model_processor=self.caption_model_processor,
                            prompt=None,
                            batch_size=32
                        )
                        
                        # Create UIElement objects
                        for i, (box, caption) in enumerate(zip(normalized_boxes, parsed_content)):
                            x1, y1, x2, y2, confidence = box
                            
                            # Convert back to pixel coordinates
                            h, w = image_np.shape[:2]
                            pixel_x1, pixel_y1 = x1 * w, y1 * h
                            pixel_x2, pixel_y2 = x2 * w, y2 * h
                            
                            element = UIElement(
                                bbox=[float(pixel_x1), float(pixel_y1), float(pixel_x2), float(pixel_y2)],
                                description=caption if caption else f"UI Element {i+1}",
                                confidence=float(confidence)
                            )
                            elements.append(element)
                            
                            logger.debug(f"Detected element {i}: {caption} at {[pixel_x1, pixel_y1, pixel_x2, pixel_y2]}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to generate captions: {e}")
                        # Fallback: create elements without detailed captions
                        for i, box in enumerate(normalized_boxes):
                            x1, y1, x2, y2, confidence = box
                            h, w = image_np.shape[:2]
                            pixel_x1, pixel_y1 = x1 * w, y1 * h
                            pixel_x2, pixel_y2 = x2 * w, y2 * h
                            
                            element = UIElement(
                                bbox=[float(pixel_x1), float(pixel_y1), float(pixel_x2), float(pixel_y2)],
                                description=f"UI Element {i+1}",
                                confidence=float(confidence)
                            )
                            elements.append(element)
        
        # Extract OCR text for each element
        if self.ocr_reader:
            elements = self._extract_ocr_text(image_path, elements)
        
        # Classify UI element types
        elements = self._classify_element_types(elements)
        
        # Merge overlapping/duplicate elements
        elements = self._merge_overlapping_elements(elements)
        
        logger.info(f"Detected {len(elements)} elements")
        return elements
    
    def get_element_at_position(self, elements: List[UIElement], x: float, y: float) -> Optional[UIElement]:
        """Find element at specific position"""
        for element in elements:
            x1, y1, x2, y2 = element.bbox
            if x1 <= x <= x2 and y1 <= y <= y2:
                return element
        return None
    
    def filter_elements_by_confidence(self, elements: List[UIElement], min_confidence: float = 0.5) -> List[UIElement]:
        """Filter elements by confidence threshold"""
        return [e for e in elements if e.confidence >= min_confidence]
    
    def _merge_overlapping_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """Merge overlapping or very close elements that are likely duplicates"""
        if len(elements) <= 1:
            return elements
        
        merged_elements = []
        used_indices = set()
        
        for i, element1 in enumerate(elements):
            if i in used_indices:
                continue
                
            # Find all elements that overlap or are very close to this one
            overlapping_group = [element1]
            group_indices = [i]
            
            for j, element2 in enumerate(elements):
                if j <= i or j in used_indices:
                    continue
                    
                if self._should_merge_elements(element1, element2):
                    overlapping_group.append(element2)
                    group_indices.append(j)
            
            # If we found overlapping elements, merge them
            if len(overlapping_group) > 1:
                merged_element = self._merge_element_group(overlapping_group)
                merged_elements.append(merged_element)
                used_indices.update(group_indices)
                logger.debug(f"Merged {len(overlapping_group)} overlapping elements")
            else:
                merged_elements.append(element1)
                used_indices.add(i)
        
        logger.info(f"Element merging: {len(elements)} → {len(merged_elements)} elements")
        return merged_elements
    
    def _should_merge_elements(self, elem1: UIElement, elem2: UIElement) -> bool:
        """Determine if two elements should be merged based on overlap and similarity"""
        # Calculate overlap ratio
        overlap_ratio = self._calculate_overlap_ratio(elem1.bbox, elem2.bbox)
        
        # Calculate center distance as percentage of image
        center1_x = (elem1.bbox[0] + elem1.bbox[2]) / 2
        center1_y = (elem1.bbox[1] + elem1.bbox[3]) / 2
        center2_x = (elem2.bbox[0] + elem2.bbox[2]) / 2
        center2_y = (elem2.bbox[1] + elem2.bbox[3]) / 2
        
        # Use a reasonable image size estimate for distance calculation
        distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5
        
        # Merge criteria:
        # 1. High overlap (>50%)
        # 2. Very close centers (<30 pixels) with same OCR text
        # 3. Same OCR text and similar confidence
        
        high_overlap = overlap_ratio > 0.5
        close_centers = distance < 30 and elem1.ocr_text == elem2.ocr_text and elem1.ocr_text != ""
        same_text_similar_conf = (elem1.ocr_text == elem2.ocr_text and 
                                 elem1.ocr_text != "" and
                                 abs(elem1.confidence - elem2.confidence) < 0.2)
        
        return high_overlap or close_centers or same_text_similar_conf
    
    def _calculate_overlap_ratio(self, bbox1: List[float], bbox2: List[float]) -> float:
        """Calculate the overlap ratio between two bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection
        x1_int = max(x1_1, x1_2)
        y1_int = max(y1_1, y1_2)
        x2_int = min(x2_1, x2_2)
        y2_int = min(y2_1, y2_2)
        
        if x2_int <= x1_int or y2_int <= y1_int:
            return 0.0  # No overlap
        
        intersection_area = (x2_int - x1_int) * (y2_int - y1_int)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = area1 + area2 - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0
    
    def _merge_element_group(self, elements: List[UIElement]) -> UIElement:
        """Merge a group of overlapping elements into a single element"""
        # Use the element with highest confidence as base
        best_element = max(elements, key=lambda e: e.confidence)
        
        # Calculate merged bounding box (union of all boxes)
        min_x1 = min(e.bbox[0] for e in elements)
        min_y1 = min(e.bbox[1] for e in elements)
        max_x2 = max(e.bbox[2] for e in elements)
        max_y2 = max(e.bbox[3] for e in elements)
        
        # Use the longest OCR text found
        ocr_texts = [e.ocr_text for e in elements if e.ocr_text.strip()]
        merged_ocr = max(ocr_texts, key=len) if ocr_texts else best_element.ocr_text
        
        # Use highest confidence
        max_confidence = max(e.confidence for e in elements)
        
        # Use the most specific element type (prefer non-container types)
        element_types = [e.element_type for e in elements]
        merged_type = best_element.element_type
        for et in element_types:
            if et not in ['container', 'interactive']:
                merged_type = et
                break
        
        return UIElement(
            bbox=[min_x1, min_y1, max_x2, max_y2],
            description=best_element.description,
            confidence=max_confidence,
            element_type=merged_type,
            ocr_text=merged_ocr
        )
    
    def _extract_ocr_text(self, image_path: str, elements: List[UIElement]) -> List[UIElement]:
        """Extract OCR text from each detected element"""
        if not self.ocr_reader:
            return elements
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not read image for OCR: {image_path}")
            return elements
        
        # Convert BGR to RGB for OCR
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        for element in elements:
            x1, y1, x2, y2 = element.bbox
            
            # Add padding around the bounding box
            padding = 5
            x1 = max(0, int(x1) - padding)
            y1 = max(0, int(y1) - padding)
            x2 = min(image.shape[1], int(x2) + padding)
            y2 = min(image.shape[0], int(y2) + padding)
            
            # Crop the element region
            cropped = image_rgb[y1:y2, x1:x2]
            
            if cropped.size == 0:
                continue
            
            try:
                # Extract text using OCR
                result = self.ocr_reader.readtext(cropped)
                
                # Combine all text found in the element
                texts = []
                for detection in result:
                    bbox, text, confidence = detection
                    if confidence > 0.5:  # Filter low confidence OCR results
                        texts.append(text.strip())
                
                # Join all text found in this element
                element.ocr_text = " ".join(texts) if texts else ""
                
            except Exception as e:
                logger.debug(f"OCR extraction failed for element: {e}")
                element.ocr_text = ""
        
        return elements
    
    def _classify_element_types(self, elements: List[UIElement]) -> List[UIElement]:
        """Classify UI elements based on OCR text and visual characteristics"""
        for element in elements:
            element_type = self._determine_element_type(element)
            element.element_type = element_type
        
        return elements
    
    def _determine_element_type(self, element: UIElement) -> str:
        """Determine the type of UI element based on text content and characteristics"""
        ocr_text = element.ocr_text.lower().strip()
        bbox = element.bbox
        
        # Calculate aspect ratio and size
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        aspect_ratio = width / height if height > 0 else 1
        area = width * height
        
        # Button indicators
        button_keywords = [
            'prihlásiť', 'prihlasit', 'login', 'submit', 'send', 'odoslať', 'odoslat',
            'potvrdiť', 'potvrdit', 'confirm', 'ok', 'cancel', 'zrušiť', 'zrusit',
            'uložiť', 'ulozit', 'save', 'delete', 'vymazať', 'vymazat', 'edit',
            'upraviť', 'upravit', 'add', 'pridať', 'pridat', 'remove', 'odstrániť',
            'odstranit', 'close', 'zatvoriť', 'zatvorit', 'open', 'otvoriť', 'otvorit'
        ]
        
        # Input field indicators
        input_keywords = [
            'meno', 'name', 'heslo', 'password', 'email', 'telefón', 'telefon', 'phone',
            'adresa', 'address', 'text', 'správa', 'sprava', 'message', 'komentár',
            'komentar', 'comment', 'popis', 'description', 'hľadať', 'hladat', 'search'
        ]
        
        # Link indicators
        link_keywords = [
            'http', 'www', 'link', 'odkaz', 'viac', 'more', 'info', 'informácie',
            'informacie', 'detail', 'podrobnosti', 'manual', 'manuál', 'návod',
            'navod', 'help', 'pomoc', 'kontakt', 'contact'
        ]
        
        # Checkbox/radio indicators
        checkbox_keywords = [
            'checkbox', 'check', 'select', 'vybrať', 'vybrat', 'označiť', 'oznacit',
            'súhlas', 'suhlas', 'agree', 'podmienky', 'terms', 'privacy', 'súkromie',
            'sukromie'
        ]
        
        # Label indicators (usually descriptive text)
        label_keywords = [
            'label', 'nadpis', 'title', 'názov', 'nazov', 'popis', 'description',
            'text', 'informácia', 'informacia', 'info'
        ]
        
        # Phone number pattern
        phone_pattern = any(char.isdigit() for char in ocr_text) and (
            '+' in ocr_text or len([c for c in ocr_text if c.isdigit()]) >= 6
        )
        
        # Email pattern
        email_pattern = '@' in ocr_text and '.' in ocr_text
        
        # Classification logic
        if not ocr_text:
            # No text - classify by size and aspect ratio
            if aspect_ratio > 3:  # Very wide elements
                return "banner"
            elif aspect_ratio < 0.5:  # Very tall elements
                return "icon"
            elif area < 2000:  # Small elements
                return "icon"
            else:
                return "container"
        
        # Text-based classification
        if any(keyword in ocr_text for keyword in button_keywords):
            return "button"
        elif any(keyword in ocr_text for keyword in input_keywords):
            return "text_input"
        elif any(keyword in ocr_text for keyword in link_keywords):
            return "link"
        elif any(keyword in ocr_text for keyword in checkbox_keywords):
            return "checkbox"
        elif phone_pattern:
            return "phone_number"
        elif email_pattern:
            return "email"
        elif ocr_text.upper() in ['SK', 'EN', 'DE', 'CZ']:  # Language selectors
            return "dropdown"
        elif len(ocr_text.split()) > 5:  # Long text
            return "text_block"
        elif ocr_text.isdigit():
            return "number"
        elif aspect_ratio > 2:  # Wide text elements
            return "text_field"
        else:
            # Default classification based on size
            if area < 1000:
                return "icon"
            elif aspect_ratio > 2:
                return "text_field"
            else:
                return "label"
    
    def save_annotated_image(self, image_path: str, elements: List[UIElement], output_path: str):
        """
        Save screenshot with bounding boxes drawn on detected elements
        
        Args:
            image_path: Path to original screenshot
            elements: List of detected UI elements
            output_path: Path to save annotated image
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not read image: {image_path}")
            return
        
        # Define colors for different element types
        type_colors = {
            'button': (0, 255, 0),           # Green
            'text_input': (255, 0, 0),       # Blue  
            'link': (0, 0, 255),             # Red
            'phone_number': (255, 255, 0),   # Cyan
            'dropdown': (255, 0, 255),       # Magenta
            'label': (128, 0, 255),         # Yellow
            'banner': (128, 128, 128),       # Gray
            'container': (64, 64, 64),       # Dark Gray
            'checkbox': (0, 128, 255),       # Orange
            'email': (128, 0, 255),          # Purple
            'text_block': (255, 128, 0),     # Light Blue
            'text_field': (0, 128, 128),     # Dark Cyan
            'icon': (128, 255, 0),           # Light Green
            'number': (255, 255, 255),       # White
            'interactive': (0, 128, 255)
        }
        
        # Draw bounding boxes and labels
        for i, element in enumerate(elements):
            x1, y1, x2, y2 = element.bbox
            # Get color based on element type, fallback to light gray
            color = type_colors.get(element.element_type, (200, 200, 200))
            
            # Draw rectangle
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            
            # Calculate center as percentage
            center_x_pct = ((element.bbox[0] + element.bbox[2]) / 2) / image.shape[1] * 100
            center_y_pct = ((element.bbox[1] + element.bbox[3]) / 2) / image.shape[0] * 100
            
            # Prepare label text with OCR text and element type
            ocr_text = element.ocr_text[:20] + "..." if len(element.ocr_text) > 20 else element.ocr_text
            if ocr_text:
                label = f"{i+1}: {ocr_text}"
            else:
                label = f"{i+1}: {element.description[:30]}..." if len(element.description) > 30 else f"{i+1}: {element.description}"
            conf_text = f"({element.confidence:.2f}) [{element.element_type}] ({center_x_pct:.0f}%, {center_y_pct:.0f}%)"
            
            # Calculate text size and position
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            
            # Draw label background
            (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, thickness)
            cv2.rectangle(image, (int(x1), int(y1) - text_height - 5), 
                         (int(x1) + text_width, int(y1)), color, -1)
            
            # Draw label text
            cv2.putText(image, label, (int(x1), int(y1) - 5), 
                       font, font_scale, (255, 255, 255), thickness)
            
            # Draw confidence below the box
            cv2.putText(image, conf_text, (int(x1), int(y2) + 15), 
                       font, font_scale, color, thickness)
        
        # Add legend to show color meanings
        self._add_color_legend(image, type_colors, elements)
        
        # Save annotated image
        cv2.imwrite(output_path, image)
        logger.info(f"Saved annotated image to: {output_path}")
        
        # Also save a summary
        summary_path = output_path.replace('.png', '_summary.txt')
        with open(summary_path, 'w') as f:
            f.write(f"OmniParser Detection Results\n")
            f.write(f"Image: {image_path}\n")
            f.write(f"Image dimensions: {image.shape[1]}x{image.shape[0]}\n")
            f.write(f"Total elements detected: {len(elements)}\n\n")
            for i, element in enumerate(elements):
                # Calculate center as percentage
                center_x_pct = ((element.bbox[0] + element.bbox[2]) / 2) / image.shape[1] * 100
                center_y_pct = ((element.bbox[1] + element.bbox[3]) / 2) / image.shape[0] * 100
                center_x_px = (element.bbox[0] + element.bbox[2]) / 2
                center_y_px = (element.bbox[1] + element.bbox[3]) / 2
                
                f.write(f"Element {i+1}:\n")
                f.write(f"  Description: {element.description}\n")
                f.write(f"  OCR Text: {element.ocr_text}\n")
                f.write(f"  Element Type: {element.element_type}\n")
                f.write(f"  Confidence: {element.confidence:.3f}\n")
                f.write(f"  BBox: {element.bbox}\n")
                f.write(f"  Center (pixels): ({center_x_px:.1f}, {center_y_px:.1f})\n")
                f.write(f"  Center (percentage): ({center_x_pct:.0f}%, {center_y_pct:.0f}%)\n\n")
        
        logger.info(f"Saved detection summary to: {summary_path}")
    
    def _add_color_legend(self, image, type_colors, elements):
        """Add a color legend to the image showing element type colors"""
        # Get unique element types from detected elements
        detected_types = set(element.element_type for element in elements)
        
        if not detected_types:
            return
        
        # Legend parameters
        legend_x = 10
        legend_y = 10
        line_height = 25
        legend_width = 200
        
        # Calculate legend height
        legend_height = len(detected_types) * line_height + 20
        
        # Draw legend background
        cv2.rectangle(image, (legend_x - 5, legend_y - 5), 
                     (legend_x + legend_width, legend_y + legend_height), 
                     (255, 255, 255), -1)  # White background
        cv2.rectangle(image, (legend_x - 5, legend_y - 5), 
                     (legend_x + legend_width, legend_y + legend_height), 
                     (0, 0, 0), 2)  # Black border
        
        # Add title
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        cv2.putText(image, "Element Types:", (legend_x, legend_y + 15), 
                   font, font_scale, (0, 0, 0), 1)
        
        # Add legend items
        y_pos = legend_y + 35
        for element_type in sorted(detected_types):
            color = type_colors.get(element_type, (200, 200, 200))
            
            # Draw color square
            cv2.rectangle(image, (legend_x, y_pos - 8), 
                         (legend_x + 15, y_pos + 2), color, -1)
            cv2.rectangle(image, (legend_x, y_pos - 8), 
                         (legend_x + 15, y_pos + 2), (0, 0, 0), 1)
            
            # Draw text
            cv2.putText(image, element_type, (legend_x + 20, y_pos), 
                       font, font_scale, (0, 0, 0), 1)
            
            y_pos += line_height
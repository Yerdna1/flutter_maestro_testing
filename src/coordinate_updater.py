"""
Coordinate Updater - Updates environment variables in main flow files with analyzed coordinates
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re

from src.vision import UIElement
from src.matcher import UIElementMatcher

logger = logging.getLogger(__name__)

class FlowCoordinateUpdater:
    """Updates coordinate environment variables in Maestro flow files"""
    
    def __init__(self):
        self.matcher = UIElementMatcher()
        
        # Mapping of coordinate variables to search terms
        self.coordinate_mappings = {
            'SEARCH_DOCTOR_X': 'Vyhľadať Lekára',
            'SEARCH_DOCTOR_Y': 'Vyhľadať Lekára',
            'PATIENT_ID_X': 'Zadajte RC/ID',
            'PATIENT_ID_Y': 'Zadajte RC/ID',
            'NEW_ORDER_X': 'Nová objednávka',
            'NEW_ORDER_Y': 'Nová objednávka',
            'CATEGORY_X': 'Biochémia a Klinická biológia',
            'CATEGORY_Y': 'Biochémia a Klinická biológia',
        }
    
    def analyze_screenshot_for_coordinates(self, screenshot_path: Path, elements: List[UIElement], 
                                         target_descriptions: List[str]) -> Dict[str, str]:
        """
        Analyze a screenshot and return coordinate mappings for target elements
        
        Args:
            screenshot_path: Path to screenshot file
            elements: List of detected UI elements
            target_descriptions: List of element descriptions to find
            
        Returns:
            Dictionary mapping coordinate variable names to percentage values
        """
        coordinates = {}
        
        # Get image dimensions for coordinate conversion
        from PIL import Image
        with Image.open(screenshot_path) as img:
            width, height = img.size
        
        for description in target_descriptions:
            # Find matching element
            match_result = self.matcher.find_best_match(description, elements)
            
            if match_result and match_result.element:
                element = match_result.element
                
                # Calculate percentage coordinates
                x1, y1, x2, y2 = element.bbox
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                percent_x = int((center_x / width) * 100)
                percent_y = int((center_y / height) * 100)
                
                # Map to coordinate variables
                for var_name, search_term in self.coordinate_mappings.items():
                    if search_term.lower() in description.lower():
                        if var_name.endswith('_X'):
                            coordinates[var_name] = str(percent_x)
                        elif var_name.endswith('_Y'):
                            coordinates[var_name] = str(percent_y)
                
                logger.info(f"Found coordinates for '{description}': {percent_x}%, {percent_y}%")
            else:
                logger.warning(f"No element found for '{description}'")
        
        return coordinates
    
    def update_main_flow_coordinates(self, main_flow_path: Path, coordinate_updates: Dict[str, str]):
        """
        Update coordinate environment variables in the main flow file
        
        Args:
            main_flow_path: Path to main flow YAML file
            coordinate_updates: Dictionary of variable name -> coordinate value mappings
        """
        if not main_flow_path.exists():
            logger.error(f"Main flow file not found: {main_flow_path}")
            return
        
        # Read the YAML file
        with open(main_flow_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update coordinate values using regex substitution
        for var_name, new_value in coordinate_updates.items():
            # Pattern to match environment variable definitions
            pattern = rf'(\s*{var_name}:\s*")[^"]*(")'
            replacement = rf'\g<1>{new_value}\g<2>'
            
            content = re.sub(pattern, replacement, content)
            logger.info(f"Updated {var_name}: {new_value}")
        
        # Write back to file
        with open(main_flow_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Updated coordinates in {main_flow_path}")
    
    def analyze_and_update_flow(self, screenshot_analysis_results: Dict[str, List[UIElement]], 
                               main_flow_path: Path):
        """
        Analyze multiple screenshots and update the main flow with coordinates
        
        Args:
            screenshot_analysis_results: Dict mapping screenshot paths to detected elements
            main_flow_path: Path to main flow file to update
        """
        all_coordinates = {}
        
        # Define which elements to look for in which screenshots
        screenshot_targets = {
            'objednavka_step_11': ['Vyhľadať Lekára', 'Zadajte RC/ID', 'Nová objednávka'],
            'objednavka_step_20': ['Biochémia a Klinická biológia']
        }
        
        # Process each screenshot
        for screenshot_path_str, elements in screenshot_analysis_results.items():
            screenshot_path = Path(screenshot_path_str)
            screenshot_name = screenshot_path.stem
            
            # Find which targets apply to this screenshot
            targets = []
            for key, target_list in screenshot_targets.items():
                if key in screenshot_name:
                    targets = target_list
                    break
            
            if targets:
                logger.info(f"Analyzing {screenshot_path} for targets: {targets}")
                coordinates = self.analyze_screenshot_for_coordinates(
                    screenshot_path, elements, targets
                )
                all_coordinates.update(coordinates)
        
        # Update the main flow file
        if all_coordinates:
            self.update_main_flow_coordinates(main_flow_path, all_coordinates)
            logger.info(f"Updated {len(all_coordinates)} coordinates in main flow")
        else:
            logger.warning("No coordinates found to update")
    
    def create_coordinate_config(self, coordinates: Dict[str, str], config_path: Path):
        """
        Create a separate coordinate configuration file
        
        Args:
            coordinates: Dictionary of coordinate mappings
            config_path: Path where to save the configuration
        """
        config = {
            'coordinates': coordinates,
            'description': 'Coordinate configuration for Maestro flows',
            'generated_by': 'ScreenAI coordinate analysis'
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Created coordinate configuration: {config_path}")


def update_flow_coordinates_from_analysis(analysis_file: Path, main_flow: Path):
    """
    Convenience function to update flow coordinates from analysis results
    
    Args:
        analysis_file: Path to analysis results file
        main_flow: Path to main flow file to update
    """
    updater = FlowCoordinateUpdater()
    
    # Load analysis results (this would depend on your analysis file format)
    # For now, this is a placeholder - you'd implement based on your analysis output format
    logger.info(f"Loading analysis from {analysis_file}")
    
    # Example: if analysis_file contains screenshot->elements mapping
    # screenshot_results = load_analysis_results(analysis_file)
    # updater.analyze_and_update_flow(screenshot_results, main_flow)
    
    logger.info("Coordinate update completed")


if __name__ == "__main__":
    # Example usage
    main_flow_path = Path("flows/objednavka_main.yaml")
    
    # Example coordinate updates
    test_coordinates = {
        'SEARCH_DOCTOR_X': '45',
        'SEARCH_DOCTOR_Y': '30',
        'PATIENT_ID_X': '45', 
        'PATIENT_ID_Y': '40',
        'NEW_ORDER_X': '50',
        'NEW_ORDER_Y': '60',
        'CATEGORY_X': '55',
        'CATEGORY_Y': '70'
    }
    
    updater = FlowCoordinateUpdater()
    updater.update_main_flow_coordinates(main_flow_path, test_coordinates)
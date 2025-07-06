#!/usr/bin/env python3
"""
Main application for ScreenAI Test Automation Tool
"""
import logging
from .colored_logger import setup_colored_logging
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from src.parser import TestCaseParser, TestAction, ActionType
from src.screenshot import ScreenshotCapture
from src.vision import OmniParserVision
from src.matcher import UIElementMatcher
from src.generator import MaestroFlowGenerator

# Configure logging
# Setup colored logging
logger = setup_colored_logging()

class ScreenAIOrchestrator:
    """Main orchestrator for the ScreenAI test automation workflow"""
    
    def __init__(self, debug: bool = False, continue_session: bool = False):
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        self.parser = TestCaseParser()
        self.screenshot = ScreenshotCapture()
        self.vision = OmniParserVision()
        self.matcher = UIElementMatcher()
        self.generator = MaestroFlowGenerator()
        
        # State tracking
        self.current_url = None
        self.screenshot_counter = 0
        self.element_mappings = {}
        self.image_dimensions = {}
        self.continue_session = continue_session
    
    def process_test_case(self, test_file: Path) -> str:
        """
        Process a single test case file
        
        Args:
            test_file: Path to the test case file
            
        Returns:
            Path to the generated Maestro flow file
        """
        logger.info(f"Processing test case: {test_file.name}")
        
        # Parse test case
        actions = self.parser.parse_file(test_file)
        warnings = self.parser.validate_actions(actions)
        
        if warnings:
            logger.warning("Test case validation warnings:")
            for warning in warnings:
                logger.warning(f"  {warning}")
        
        test_name = test_file.stem
        
        # Process each action
        for i, action in enumerate(actions):
            logger.info(f"Processing action {i+1}/{len(actions)}: {action.action_type.value}")
            
            try:
                self._process_action(action, i)
            except Exception as e:
                logger.error(f"Error processing action {i+1}: {e}")
                if action.action_type == ActionType.OPEN:
                    # Critical error - can't continue
                    raise
                else:
                    # Non-critical error - continue with next action
                    continue
        
        # Generate Maestro flow
        logger.info(f"Element mappings found: {len(self.element_mappings)}")
        for action_idx, element in self.element_mappings.items():
            logger.info(f"  Action {action_idx}: {element.description} at {element.bbox} with OCR: '{element.ocr_text}'")
        
        flow_file = self.generator.generate_flow(
            test_name=test_name,
            actions=actions,
            element_mappings=self.element_mappings,
            image_dimensions=self.image_dimensions,
            app_id=None  # Web application
        )
        
        logger.info(f"Test case processing complete: {flow_file}")
        return flow_file
    
    def _process_action(self, action: TestAction, action_index: int):
        """Process a single test action"""
        
        if action.action_type == ActionType.OPEN:
            if not self.continue_session:
                self.current_url = action.target
                self.screenshot.open_url(action.target)
            else:
                logger.info(f"Continuing from existing session, skipping URL open: {action.target}")
            
        elif action.action_type == ActionType.WAIT:
            self.screenshot.wait(action.wait_time)
            
        elif action.action_type == ActionType.SCREENSHOT:
            self._take_screenshot_and_analyze(action_index)
            
        elif action.action_type == ActionType.MAESTRO_SCREENSHOT:
            # This will generate takeScreenshot in YAML and also analyze
            self._take_screenshot_and_analyze(action_index)
            
        elif action.action_type == ActionType.ANALYZE:
            # Handle both "call omniparser" and "annotated screenshot" commands
            if action.target == "current_screenshot":
                self._annotate_current_screenshot(action_index)
            else:
                self._analyze_existing_screenshot(action.target, action_index)
            
        elif action.action_type in [ActionType.TAP, ActionType.CLICK]:
            # For TAP/CLICK actions, use the most recent screenshot dimensions
            if action_index not in self.image_dimensions:
                # Use dimensions from the most recent screenshot
                if hasattr(self, 'current_screenshot_action') and self.current_screenshot_action in self.image_dimensions:
                    self.image_dimensions[action_index] = self.image_dimensions[self.current_screenshot_action]
                    logger.info(f"Using dimensions from screenshot {self.current_screenshot_action} for action {action_index}")
                else:
                    # If no screenshot taken yet, take one now
                    self._take_screenshot_and_analyze(action_index)
            
            # Find matching element
            if action.target:
                element_mapping = self._find_element_for_action(action.target, action_index)
                if element_mapping:
                    self.element_mappings[action_index] = element_mapping
                    logger.info(f"Found element for '{action.target}': {element_mapping.description} with OCR: '{element_mapping.ocr_text}'")
                else:
                    # Try to find element by OCR text or element type
                    element_mapping = self._find_element_by_ocr_or_type(action.target, action_index)
                    if element_mapping:
                        self.element_mappings[action_index] = element_mapping
                        logger.info(f"Found element by OCR/type for '{action.target}': {element_mapping.ocr_text}")
                    else:
                        logger.warning(f"No element found for '{action.target}'")
            
        elif action.action_type == ActionType.ENTER:
            # For enter actions, we don't need to find elements
            # The previous action should have found the input field
            pass
            
        elif action.action_type == ActionType.FIND:
            # Take screenshot and find element
            if action_index not in self.image_dimensions:
                self._take_screenshot_and_analyze(action_index)
            
            if action.target:
                element_mapping = self._find_element_for_action(action.target, action_index)
                if element_mapping:
                    self.element_mappings[action_index] = element_mapping
                    logger.info(f"Found element for '{action.target}': {element_mapping.description}")
    
    def _take_screenshot_and_analyze(self, action_index: int):
        """Take screenshot and analyze UI elements"""
        self.screenshot_counter += 1
        
        # Take screenshot
        screenshot_path, dimensions = self.screenshot.take_screenshot(
            f"step_{self.screenshot_counter:02d}"
        )
        
        self.image_dimensions[action_index] = dimensions
        
        # Analyze screenshot with OmniParser
        logger.info(f"Analyzing screenshot: {screenshot_path}")
        elements = self.vision.detect_elements(screenshot_path)
        
        # Store elements for this action - keep separate analyses for each screenshot
        if not hasattr(self, 'detected_elements'):
            self.detected_elements = {}
        self.detected_elements[action_index] = elements
        
        # Also update the current elements set for subsequent actions until next screenshot
        self.current_elements = elements
        self.current_screenshot_action = action_index
        
        # Save analyzed image with bounding boxes
        analyzed_path = screenshot_path.replace('.png', '_analyzed.png')
        self.vision.save_annotated_image(screenshot_path, elements, analyzed_path)
        
        logger.info(f"Screenshot {self.screenshot_counter} analyzed - Found {len(elements)} UI elements")
        for i, element in enumerate(elements):
            logger.debug(f"  Element {i+1}: {element.description} (confidence: {element.confidence:.2f}) - Type: {element.element_type}, OCR: '{element.ocr_text}', Bbox: {element.bbox}")
    
    def _analyze_existing_screenshot(self, screenshot_reference: str, action_index: int):
        """Analyze an existing screenshot file with OmniParser"""
        import glob
        from pathlib import Path
        
        # Handle special case for current screenshot
        if screenshot_reference == "current_screenshot":
            # Use the most recent screenshot taken
            if hasattr(self, 'current_screenshot_action') and self.current_screenshot_action in self.detected_elements:
                # Re-analyze the current screenshot to get fresh elements
                screenshot_path = f"screenshots/step_{self.screenshot_counter:02d}.png"
                if Path(screenshot_path).exists():
                    logger.info(f"Re-analyzing current screenshot: {screenshot_path}")
                else:
                    logger.warning(f"Current screenshot not found: {screenshot_path}")
                    return
            else:
                logger.warning("No current screenshot available for analysis")
                return
        else:
            # Extract screenshot filename pattern from reference
            # Handle formats like "testCase1_step_10_2025....png screenshot" 
            screenshot_pattern = screenshot_reference.strip().replace('"', '').replace('screenshot', '').strip()
            
            # Try to find matching screenshot files
            screenshot_files = []
            
            # Look for exact match first
            if Path(screenshot_pattern).exists():
                screenshot_files = [screenshot_pattern]
            else:
                # Try to find files matching the pattern
                if "..." in screenshot_pattern:
                    # Replace "..." with wildcard
                    pattern = screenshot_pattern.replace("....", "*")
                    screenshot_files = glob.glob(pattern)
                
                # If no match, try looking in screenshots directory
                if not screenshot_files:
                    screenshots_dir = Path("screenshots")
                    if "testCase1_step_10" in screenshot_pattern:
                        # Look for testCase1 step 10 screenshots
                        screenshot_files = list(screenshots_dir.glob("*step_02*.png"))  # step_02 is the post-login screenshot
            
            if not screenshot_files:
                logger.warning(f"No screenshot found matching pattern: {screenshot_pattern}")
                return
            
            # Use the most recent matching screenshot
            screenshot_path = str(sorted(screenshot_files)[-1])
        
        logger.info(f"Analyzing existing screenshot: {screenshot_path}")
        
        # Detect elements in the existing screenshot
        elements = self.vision.detect_elements(screenshot_path)
        
        # Get image dimensions
        from PIL import Image
        with Image.open(screenshot_path) as image:
            dimensions = image.size
        
        self.image_dimensions[action_index] = dimensions
        
        # Store elements for this action
        if not hasattr(self, 'detected_elements'):
            self.detected_elements = {}
        self.detected_elements[action_index] = elements
        
        # Also update the current elements set for subsequent actions
        self.current_elements = elements
        self.current_screenshot_action = action_index
        
        # Save annotated image
        annotated_path = screenshot_path.replace('.png', '_analyzed.png')
        self.vision.save_annotated_image(screenshot_path, elements, annotated_path)
        
        logger.info(f"Analyzed existing screenshot - Found {len(elements)} UI elements")
        for i, element in enumerate(elements):
            logger.debug(f"  Element {i+1}: {element.description} (confidence: {element.confidence:.2f}) - Type: {element.element_type}, OCR: '{element.ocr_text}', Bbox: {element.bbox}")
    
    def _annotate_current_screenshot(self, action_index: int):
        """Annotate the most recent screenshot with fresh element detection"""
        if not hasattr(self, 'screenshot_counter') or self.screenshot_counter == 0:
            logger.warning("No screenshots taken yet - cannot annotate")
            return
        
        # Use the most recent screenshot
        screenshot_path = f"screenshots/step_{self.screenshot_counter:02d}.png"
        
        if not Path(screenshot_path).exists():
            logger.warning(f"Screenshot not found for annotation: {screenshot_path}")
            return
        
        logger.info(f"Annotating current screenshot: {screenshot_path}")
        
        # Detect elements in the current screenshot with fresh analysis
        elements = self.vision.detect_elements(screenshot_path)
        
        # Get image dimensions
        from PIL import Image
        with Image.open(screenshot_path) as image:
            dimensions = image.size
        
        self.image_dimensions[action_index] = dimensions
        
        # Store elements for this action
        if not hasattr(self, 'detected_elements'):
            self.detected_elements = {}
        self.detected_elements[action_index] = elements
        
        # Update the current elements set for subsequent actions
        self.current_elements = elements
        self.current_screenshot_action = action_index
        
        # Fresh analysis already saved via _take_screenshot_and_analyze, skip duplicate
        
        logger.info(f"Annotated current screenshot - Found {len(elements)} UI elements")
        for i, element in enumerate(elements):
            logger.debug(f"  Element {i+1}: {element.description} (confidence: {element.confidence:.2f}) - Type: {element.element_type}, OCR: '{element.ocr_text}', Bbox: {element.bbox}")
    
    def _find_element_for_action(self, target_description: str, action_index: int):
        """Find the best matching element for an action"""
        # Use elements from the most recent screenshot analysis
        elements = None
        
        if action_index in self.detected_elements:
            elements = self.detected_elements[action_index]
        elif hasattr(self, 'current_elements'):
            elements = self.current_elements
            logger.info(f"Using current elements from screenshot {getattr(self, 'current_screenshot_action', 'unknown')} for action {action_index}")
        
        if not elements:
            logger.warning(f"No elements available for action {action_index}")
            return None
        
        match_result = self.matcher.find_best_match(target_description, elements)
        
        if match_result:
            return match_result.element
        return None
    
    def _find_element_by_ocr_or_type(self, target_description: str, action_index: int):
        """Find element using improved matcher with Slovak support"""
        # Use elements from the most recent screenshot analysis
        elements = None
        
        if action_index in self.detected_elements:
            elements = self.detected_elements[action_index]
        elif hasattr(self, 'current_elements'):
            elements = self.current_elements
        
        if not elements:
            return None
            
        # Use the improved matcher with Slovak support
        match_result = self.matcher.find_best_match(target_description, elements)
        
        if match_result:
            return match_result.element
        return None
    
    def cleanup(self):
        """Clean up resources"""
        if not self.continue_session:
            self.screenshot.close()
        else:
            logger.info("Keeping browser open for continuation")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

def analyze_screenshot_mode(args):
    """Handle screenshot analysis mode called by Maestro"""
    from src.vision import OmniParserVision
    from src.matcher import UIElementMatcher
    import yaml
    
    screenshot_path = Path(args.analyze_screenshot)
    yaml_path = Path(args.update_yaml) if args.update_yaml else None
    
    if not screenshot_path.exists():
        logger.error(f"Screenshot file does not exist: {screenshot_path}")
        sys.exit(1)
    
    logger.info(f"Analyzing screenshot: {screenshot_path}")
    
    try:
        # Initialize vision system
        vision = OmniParserVision()
        matcher = UIElementMatcher()
        
        # Analyze the screenshot
        elements = vision.detect_elements(str(screenshot_path))
        logger.info(f"Detected {len(elements)} UI elements")
        
        # Create FINISHED folder for analyzed files
        finished_dir = screenshot_path.parent / "FINISHED"
        finished_dir.mkdir(exist_ok=True)
        
        # Save analysis results directly to FINISHED folder
        analyzed_filename = screenshot_path.stem + '_analyzed.png'
        analyzed_path = finished_dir / analyzed_filename
        vision.save_annotated_image(str(screenshot_path), elements, str(analyzed_path))
        
        # Also save summary to FINISHED folder
        summary_filename = screenshot_path.stem + '_analyzed_summary.txt'
        summary_path = finished_dir / summary_filename
        if (screenshot_path.parent / (screenshot_path.stem + '_analyzed_summary.txt')).exists():
            import shutil
            shutil.move(
                str(screenshot_path.parent / (screenshot_path.stem + '_analyzed_summary.txt')),
                str(summary_path)
            )
        
        # Update YAML file if specified
        if yaml_path and yaml_path.exists():
            update_yaml_coordinates(yaml_path, elements, matcher)
            logger.info(f"Updated coordinates in {yaml_path}")
        
        logger.info(f"📁 Analysis files saved to: {finished_dir}")
        logger.info("Screenshot analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to analyze screenshot: {e}")
        sys.exit(1)

def update_yaml_coordinates(yaml_path: Path, elements, matcher):
    """Update TODO coordinates in YAML file with detected elements"""
    import yaml
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            # Handle multiple YAML documents (URL config + flow commands)
            documents = list(yaml.safe_load_all(f))
        
        if len(documents) < 2:
            logger.error("Invalid YAML structure - expected URL config and flow commands")
            return
            
        url_config = documents[0]  # First document: url config
        flow_commands = documents[1]  # Second document: flow commands list
        
        # Get screenshot dimensions from the analyzed screenshot
        from PIL import Image
        screenshot_file = None
        
        # Try to find the actual screenshot file that was analyzed
        yaml_dir = yaml_path.parent
        screenshots_dir = yaml_dir.parent / "screenshots" / "objednavka"
        
        if screenshots_dir.exists():
            # Find the most recent screenshot
            screenshot_files = list(screenshots_dir.glob("*.png"))
            if screenshot_files:
                screenshot_file = str(sorted(screenshot_files, key=lambda f: f.stat().st_mtime)[-1])
        
        if screenshot_file and Path(screenshot_file).exists():
            with Image.open(screenshot_file) as img:
                screen_width, screen_height = img.size
                logger.info(f"📏 Using screenshot dimensions: {screen_width}x{screen_height} from {Path(screenshot_file).name}")
        else:
            # Fallback to detected dimensions from analysis
            screen_width = 3492  # From latest analysis summary  
            screen_height = 1912
            logger.warning(f"📏 Using fallback dimensions: {screen_width}x{screen_height}")
        
        # Log all available OCR texts for debugging
        logger.info("🔍 Available OCR texts in screenshot:")
        for i, elem in enumerate(elements):
            logger.info(f"  {i+1:2d}: '{elem.ocr_text}' (confidence: {elem.confidence:.3f}, type: {elem.element_type})")
        
        # Find and update ALL coordinates (TODO and existing ones)
        updated_count = 0
        todo_count = 0
        existing_count = 0
        not_found_items = []
        
        for command in flow_commands:
            if isinstance(command, dict) and 'tapOn' in command:
                tap_command = command['tapOn']
                if isinstance(tap_command, dict) and 'point' in tap_command:
                    current_point = tap_command.get('point', '')
                    comment = tap_command.get('_comment', '')
                    
                    # Extract target text from comment
                    target_text = ''
                    if 'PROSIM NAJDI SURADNICE PRE' in comment:
                        target_text = comment.split('"')[1] if '"' in comment else ''
                    elif '# ' in comment:
                        # Extract from standard comment format: # Vyhľadať Lekára (OCR: ...)
                        target_text = comment.split('# ')[1].split(' (OCR:')[0] if '# ' in comment else ''
                    
                    if target_text:
                        is_todo = current_point == 'TODO%,TODO%'
                        
                        # Always try to find the element (whether TODO or existing)
                        logger.info(f"🔍 Searching for element: '{target_text}'")
                        
                        # Find matching element
                        match_result = matcher.find_best_match(target_text, elements)
                        if match_result and match_result.element:
                            element = match_result.element
                            # Calculate percentage coordinates from bbox center
                            center_x = (element.bbox[0] + element.bbox[2]) / 2
                            center_y = (element.bbox[1] + element.bbox[3]) / 2
                            
                            percent_x = (center_x / screen_width) * 100
                            percent_y = (center_y / screen_height) * 100
                            new_point = f"{percent_x:.0f}%,{percent_y:.0f}%"
                            
                            # Update the coordinates
                            old_point = tap_command['point']
                            tap_command['point'] = new_point
                            
                            # Add OCR info to comment if not already present
                            if 'OCR:' not in comment:
                                comment = f"{comment} (OCR: {element.ocr_text})"
                                tap_command['_comment'] = comment
                            
                            updated_count += 1
                            if is_todo:
                                todo_count += 1
                                logger.info(f"✅ TODO → Updated: '{target_text}' → {new_point} (matched: '{element.ocr_text}' score: {match_result.score:.1f})")
                            else:
                                existing_count += 1
                                logger.info(f"🔄 EXISTING → Updated: '{target_text}' → {old_point} → {new_point} (matched: '{element.ocr_text}' score: {match_result.score:.1f})")
                        else:
                            not_found_items.append(target_text)
                            if is_todo:
                                logger.warning(f"❌ TODO → Not found: '{target_text}'")
                            else:
                                logger.warning(f"❌ EXISTING → Not found: '{target_text}' (keeping old coordinates: {current_point})")
        
        # Log summary
        logger.info(f"📊 Update Summary:")
        logger.info(f"   ✅ Total updated: {updated_count}")
        logger.info(f"   🆕 TODO items updated: {todo_count}")
        logger.info(f"   🔄 Existing items updated: {existing_count}")
        logger.info(f"   ❌ Items not found: {len(not_found_items)}")
        
        if not_found_items:
            logger.warning(f"🔍 Still TODO/missing coordinates for:")
            for item in not_found_items:
                logger.warning(f"   - '{item}'")
        
        if updated_count > 0:
            # Write updated YAML with multiple documents
            with open(yaml_path, 'w', encoding='utf-8') as f:
                # Write URL config
                yaml.safe_dump(url_config, f, default_flow_style=False, allow_unicode=True)
                f.write('---\n')  # Document separator
                # Write flow commands
                yaml.safe_dump(flow_commands, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"💾 Saved updated coordinates to {yaml_path.name}")
        else:
            logger.info("💾 No coordinates updated - YAML file unchanged")
            
    except Exception as e:
        logger.error(f"Failed to update YAML coordinates: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ScreenAI Test Automation Tool")
    parser.add_argument("test_case", nargs='?', help="Path to test case file or directory")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--continue", action="store_true", help="Continue from existing browser session (don't open new URL)")
    parser.add_argument("--analyze-screenshot", help="Analyze a specific screenshot file")
    parser.add_argument("--update-yaml", help="Update YAML file with analysis results")
    
    args = parser.parse_args()
    
    # Handle screenshot analysis mode
    if args.analyze_screenshot:
        analyze_screenshot_mode(args)
        return
    
    # Normal test case processing mode
    if not args.test_case:
        logger.error("test_case argument is required when not using --analyze-screenshot")
        sys.exit(1)
        
    test_path = Path(args.test_case)
    
    if not test_path.exists():
        logger.error(f"Test case path does not exist: {test_path}")
        sys.exit(1)
    
    # Setup logging with debug if requested
    if args.debug:
        setup_colored_logging(debug=True)
    
    # Process test cases
    try:
        with ScreenAIOrchestrator(debug=args.debug, continue_session=getattr(args, 'continue', False)) as orchestrator:
            orchestrator.screenshot.headless = args.headless
            
            if test_path.is_file():
                # Process single file
                if test_path.suffix != '.txt':
                    logger.error("Test case files must have .txt extension")
                    sys.exit(1)
                
                flow_file = orchestrator.process_test_case(test_path)
                print(f"Generated flow: {flow_file}")
                
            elif test_path.is_dir():
                # Process all .txt files in directory
                test_files = list(test_path.glob("*.txt"))
                if not test_files:
                    logger.error(f"No .txt files found in {test_path}")
                    sys.exit(1)
                
                for test_file in test_files:
                    try:
                        flow_file = orchestrator.process_test_case(test_file)
                        print(f"Generated flow: {flow_file}")
                    except Exception as e:
                        logger.error(f"Failed to process {test_file}: {e}")
                        continue
            
            else:
                logger.error(f"Invalid test case path: {test_path}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
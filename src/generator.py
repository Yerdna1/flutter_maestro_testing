"""
Maestro Flow Generator - generates Maestro test flows from detected UI elements
"""
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from src.parser import TestAction, ActionType
from src.vision import UIElement

logger = logging.getLogger(__name__)

class MaestroFlowGenerator:
    """Generates Maestro-compatible test flows"""
    
    def __init__(self, output_dir: str = "flows"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_flow(self, 
                     test_name: str,
                     actions: List[TestAction],
                     element_mappings: Dict[int, UIElement],
                     image_dimensions: Dict[int, Tuple[int, int]],
                     app_id: Optional[str] = None) -> str:
        """
        Generate a Maestro flow file from test actions and detected elements
        
        Args:
            test_name: Name of the test case
            actions: List of parsed test actions
            element_mappings: Mapping of action index to detected UI element
            image_dimensions: Mapping of screenshot index to (width, height)
            app_id: Optional app identifier for mobile apps
            
        Returns:
            Path to generated flow file
        """
        flow_commands = []
        current_dimensions = (1920, 1080)  # Default dimensions
        
        # Determine if this is a web or mobile flow
        is_web_flow = any(action.action_type == ActionType.OPEN and 
                         action.target.startswith(('http://', 'https://')) 
                         for action in actions)
        
        # Add proper config section
        if is_web_flow:
            # For web flows, extract URL from first OPEN action
            web_url = None
            for action in actions:
                if action.action_type == ActionType.OPEN:
                    web_url = action.target
                    break
            if web_url:
                flow_commands.append({"url": web_url})
            else:
                flow_commands.append({"url": "https://example.com"})
        elif app_id:
            flow_commands.append({"appId": app_id})
        else:
            # Default mobile app
            flow_commands.append({"appId": "com.example.app"})
        
        flow_commands.append("---")
        
        # Process each action
        for i, action in enumerate(actions):
            # Update current dimensions if we have new screenshot dimensions
            if i in image_dimensions:
                current_dimensions = image_dimensions[i]
            
            # Look ahead for FIND→ENTER sequences
            next_action = actions[i + 1] if i + 1 < len(actions) else None
            
            command = self._convert_action_to_command(action, element_mappings.get(i), current_dimensions, is_web_flow, test_name, i, next_action)
            if command is not None:
                # Handle both single commands and lists of commands
                if isinstance(command, list):
                    flow_commands.extend(command)
                else:
                    flow_commands.append(command)
        
        # Write flow file
        flow_file = self.output_dir / f"{test_name}.yaml"
        self._write_flow_file(flow_file, flow_commands)
        
        logger.info(f"Generated Maestro flow: {flow_file}")
        return str(flow_file)
    
    def _convert_action_to_command(self, 
                                  action: TestAction, 
                                  element: Optional[UIElement],
                                  dimensions: Tuple[int, int],
                                  is_web_flow: bool = False,
                                  test_name: str = "test",
                                  action_index: int = 0,
                                  next_action: Optional[TestAction] = None) -> Optional[Dict[str, Any]]:
        """Convert a test action to a Maestro command"""
        
        if action.action_type == ActionType.OPEN:
            if is_web_flow:
                # For web flows, just launch the app - URL is already in config
                return "launchApp"
            else:
                return None  # Skip for mobile apps
        
        elif action.action_type == ActionType.WAIT:
            return {"waitForAnimationToEnd": {"timeout": int(action.wait_time * 1000)}}
        
        elif action.action_type == ActionType.SCREENSHOT:
            # Add a Maestro screenshot command with descriptive name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Note: Maestro automatically adds .png extension
            filename = f"screenshots/{test_name}/{test_name}_step_{action_index+1:02d}_{timestamp}"
            return {"takeScreenshot": filename}
        
        elif action.action_type == ActionType.MAESTRO_SCREENSHOT:
            # Add a Maestro screenshot command with old JavaScript analysis
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Note: Maestro automatically adds .png extension
            filename = f"screenshots/{test_name}/{test_name}_step_{action_index+1:02d}_{timestamp}"
            # Return both takeScreenshot and runScript commands using old JavaScript
            return [
                {"takeScreenshot": filename},
                {"runScript": {
                    "file": "analyze_screenshot.js",
                    "env": {
                        "SCREENSHOT_PATH": f"{filename}.png",
                        "TEST_NAME": test_name,
                        "ACTION_INDEX": str(action_index)
                    }
                }}
            ]
        
        elif action.action_type == ActionType.ANALYZE:
            # Skip analyze actions in Maestro flow - they're used for element detection only
            return None
        
        elif action.action_type == ActionType.TAP or action.action_type == ActionType.CLICK:
            if element:
                # Convert pixel coordinates to percentages (preferred for Flutter web)
                point = self._pixel_to_percentage(element.bbox, dimensions)
                logger.info(f"Using percentage coordinates for '{action.target}': {point}")
                # Add comment with original target description (more reliable than OCR)
                target_clean = action.target.replace('"', '').strip()
                ocr_info = f" (OCR: {element.ocr_text})" if element.ocr_text and element.ocr_text.strip() else ""
                return {
                    "tapOn": {
                        "point": point,
                        "_comment": f"{target_clean}{ocr_info}"  # Use target description, not unreliable OCR
                    }
                }
            else:
                # Generate placeholder tapOn when element not found
                target_clean = action.target.replace('"', '').strip()
                logger.warning(f"TAP/CLICK: No element found for '{action.target}' - generating placeholder")
                return {
                    "tapOn": {
                        "point": "TODO%,TODO%",
                        "_comment": f"PROSIM NAJDI SURADNICE PRE \"{target_clean}\""
                    }
                }
        
        elif action.action_type == ActionType.ENTER:
            return {"inputText": action.value}
        
        elif action.action_type == ActionType.FIND:
            # If FIND is followed by ENTER, generate a tapOn command
            if next_action and next_action.action_type == ActionType.ENTER:
                if element:
                    # Convert pixel coordinates to percentages (preferred for Flutter web)
                    point = self._pixel_to_percentage(element.bbox, dimensions)
                    logger.info(f"Using percentage coordinates for FIND→ENTER '{action.target}': {point}")
                    # Add comment with original target description (more reliable than OCR)
                    target_clean = action.target.replace('"', '').strip()
                    ocr_info = f" (OCR: {element.ocr_text})" if element.ocr_text and element.ocr_text.strip() else ""
                    return {
                        "tapOn": {
                            "point": point,
                            "_comment": f"{target_clean}{ocr_info}"  # Use target description, not unreliable OCR
                        }
                    }
                else:
                    # CRITICAL: Never use text-based taps. But we must generate a tapOn for FIND→ENTER sequences.
                    # Generate a placeholder tapOn that needs manual coordinate specification
                    logger.error(f"FIND→ENTER: No element found for '{action.target}' - generating placeholder tapOn (REQUIRES MANUAL COORDINATE UPDATE)")
                    # Clean target name for Slovak comment
                    target_clean = action.target.replace('"', '').strip()
                    return {
                        "tapOn": {
                            "point": "TODO%,TODO%",
                            "_comment": f"PROSIM NAJDI SURADNICE PRE \"{target_clean}\""
                        }
                    }
            else:
                # Standalone FIND actions should generate placeholder tapOn
                target_clean = action.target.replace('"', '').strip()
                logger.warning(f"FIND: Standalone find action for '{action.target}' - generating placeholder tapOn")
                return {
                    "tapOn": {
                        "point": "TODO%,TODO%",
                        "_comment": f"PROSIM NAJDI SURADNICE PRE \"{target_clean}\""
                    }
                }
        
        # This should never be reached if all action types are handled above
        logger.warning(f"Unhandled action type: {action.action_type} - this may cause missing steps in YAML")
        return None
    
    def _pixel_to_percentage(self, bbox: List[float], dimensions: Tuple[int, int]) -> str:
        """Convert pixel coordinates to percentage string for Maestro"""
        x1, y1, x2, y2 = bbox
        width, height = dimensions
        
        # Calculate center point
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Convert to percentages
        percent_x = (center_x / width) * 100
        percent_y = (center_y / height) * 100
        
        logger.info(f"Converting bbox {bbox} with dimensions {dimensions} -> center ({center_x:.1f}, {center_y:.1f}) -> {percent_x:.1f}%, {percent_y:.1f}%")
        
        return f"{percent_x:.0f}%,{percent_y:.0f}%"
    
    def _write_flow_file(self, file_path: Path, commands: List[Any]):
        """Write Maestro flow to YAML file with proper comments"""
        # Flatten nested command lists
        flattened_commands = []
        for cmd in commands:
            if isinstance(cmd, list):
                flattened_commands.extend(cmd)
            else:
                flattened_commands.append(cmd)
        
        with open(file_path, 'w') as f:
            # Write config section first
            config_written = False
            flow_commands = []
            
            for command in flattened_commands:
                if isinstance(command, dict) and ("appId" in command or "url" in command) and not config_written:
                    # Write config section without list format
                    if "url" in command:
                        f.write(f"url: {command['url']}\n")
                    else:
                        f.write(f"appId: {command['appId']}\n")
                    config_written = True
                elif command == "---":
                    f.write("---\n")
                else:
                    # Process command for comments
                    processed_command = self._process_command_comments(command)
                    flow_commands.append(processed_command)
            
            # Write flow commands with custom formatting for comments
            if flow_commands:
                self._write_commands_with_comments(f, flow_commands)
    
    def _process_command_comments(self, command):
        """Process command to extract comments for proper YAML formatting"""
        if isinstance(command, dict):
            # Create a copy without the _comment field
            processed = {}
            for key, value in command.items():
                if key != "_comment":
                    if isinstance(value, dict) and "_comment" in value:
                        # Extract comment from nested dict
                        nested = {k: v for k, v in value.items() if k != "_comment"}
                        processed[key] = nested
                        # Store comment separately
                        if not hasattr(command, '_extracted_comment'):
                            processed['_extracted_comment'] = value["_comment"]
                    else:
                        processed[key] = value
            return processed
        return command
    
    def _write_commands_with_comments(self, f, commands):
        """Write commands to file with proper YAML comment formatting"""
        for i, command in enumerate(commands):
            if isinstance(command, dict):
                # Check if this command has an extracted comment
                comment = command.pop('_extracted_comment', None)
                
                # Write the command using yaml.dump for a single item
                yaml_str = yaml.dump([command], default_flow_style=False, sort_keys=False)
                # Remove the list wrapper from yaml output
                lines = yaml_str.strip().split('\n')
                if lines[0].startswith('- '):
                    lines[0] = lines[0][2:]  # Remove '- ' prefix
                    for j in range(1, len(lines)):
                        if lines[j].startswith('  '):
                            lines[j] = lines[j][2:]  # Remove extra indentation
                
                # Add comment if present
                if comment and 'tapOn' in command:
                    # Find the point line and add comment
                    for j, line in enumerate(lines):
                        if 'point:' in line:
                            lines[j] = line + f"  # {comment}"
                            break
                
                # Write to file with proper list format
                f.write(f"- {lines[0]}\n")
                for line in lines[1:]:
                    f.write(f"  {line}\n")
            else:
                # Handle non-dict commands
                yaml_str = yaml.dump([command], default_flow_style=False, sort_keys=False)
                f.write(yaml_str)
    
    def generate_web_flow(self, test_name: str, url: str, actions: List[Dict[str, Any]]) -> str:
        """Generate a flow specifically for web testing"""
        flow_commands = [
            {"comment": f"Web test: {test_name}"},
            {"comment": f"URL: {url}"},
            {"comment": f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}, 
            {"comment": "Note: This is a web test flow. Use with a web-compatible Maestro setup."},
            {"comment": "---"},
        ]
        
        flow_commands.extend(actions)
        
        flow_file = self.output_dir / f"{test_name}_web.yaml"
        self._write_flow_file(flow_file, flow_commands)
        
        return str(flow_file)
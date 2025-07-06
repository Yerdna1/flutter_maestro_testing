"""
Test case parser module for reading and parsing test instructions from text files
"""
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    OPEN = "open"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    MAESTRO_SCREENSHOT = "maestro_screenshot"
    ANALYZE = "analyze"
    FIND = "find"
    TAP = "tap"
    ENTER = "enter"
    CLICK = "click"

@dataclass
class TestAction:
    """Represents a single test action"""
    action_type: ActionType
    target: str = ""
    value: str = ""
    wait_time: float = 0.0
    line_number: int = 0

class TestCaseParser:
    """Parse test case instructions from text files"""
    
    def __init__(self):
        self.action_patterns = {
            ActionType.OPEN: re.compile(r'open\s+(?:web\s+)?(?:application\s+)?(.+)', re.IGNORECASE),
            ActionType.WAIT: re.compile(r'wait\s+(\d+(?:\.\d+)?)\s+seconds?', re.IGNORECASE),
            ActionType.SCREENSHOT: re.compile(r'take\s+(?:a\s+)?screenshot(?:\s+with\s+name\s+"([^"]+)")?(?:\s+at\s+path\s+"([^"]+)")?', re.IGNORECASE),
            ActionType.MAESTRO_SCREENSHOT: re.compile(r'take\s+maestro\s+screenshot\s+and\s+call\s+omniparser\s+for\s+analyzing', re.IGNORECASE),
            ActionType.ANALYZE: re.compile(r'(?:call\s+omniparser\s+for\s+analyzing|annotated?\s+(?:this\s+)?screenshot\s+with\s+omniparser)', re.IGNORECASE),
            ActionType.FIND: re.compile(r'find\s+(.+?)(?:\s+and\s+(?:tap|click).*)?$', re.IGNORECASE),
            ActionType.TAP: re.compile(r'(?:tap\s*on|tap)\s+(?:it|(.+))', re.IGNORECASE),
            ActionType.CLICK: re.compile(r'(?:click\s*on|click)\s+(?:it|(.+))', re.IGNORECASE),
            ActionType.ENTER: re.compile(r'enter\s+(?:here\s+)?(.+)', re.IGNORECASE),
        }
    
    def parse_file(self, file_path: Path) -> List[TestAction]:
        """Parse a test case file and return list of actions"""
        if not file_path.exists():
            raise FileNotFoundError(f"Test case file not found: {file_path}")
        
        actions = []
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            # Remove line number prefix if present (e.g., "1-", "2.5-")
            line = re.sub(r'^\d+(?:\.\d+)?[-\s]+', '', line.strip())
            
            if not line:
                continue
            
            # Check for combined screenshot + analyze action
            screenshot_analyze_pattern = re.compile(r'take\s+(?:a\s+)?screenshot(?:\s+with\s+name\s+"([^"]+)")?(?:\s+at\s+path\s+"([^"]+)")?.*and\s+call\s+omniparser', re.IGNORECASE)
            match = screenshot_analyze_pattern.search(line)
            if match:
                # Extract screenshot name and path if provided
                screenshot_name = match.group(1) if match.group(1) else ""
                screenshot_path = match.group(2) if match.group(2) else ""
                # Add both screenshot and analyze actions
                actions.append(TestAction(
                    action_type=ActionType.SCREENSHOT,
                    target=screenshot_name,
                    value=screenshot_path,
                    line_number=line_num
                ))
                actions.append(TestAction(
                    action_type=ActionType.ANALYZE,
                    target="current_screenshot",
                    line_number=line_num
                ))
            else:
                action = self._parse_line(line, line_num)
                if action:
                    actions.append(action)
        
        return actions
    
    def _parse_line(self, line: str, line_number: int) -> TestAction:
        """Parse a single line and return TestAction if valid"""
        line = line.strip()
        
        # Check each action pattern
        for action_type, pattern in self.action_patterns.items():
            match = pattern.search(line)
            if match:
                if action_type == ActionType.OPEN:
                    return TestAction(
                        action_type=action_type,
                        target=match.group(1).strip(),
                        line_number=line_number
                    )
                
                elif action_type == ActionType.WAIT:
                    return TestAction(
                        action_type=action_type,
                        wait_time=float(match.group(1)),
                        line_number=line_number
                    )
                
                elif action_type == ActionType.SCREENSHOT:
                    name = match.group(1) if match.group(1) else ""
                    path = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                    return TestAction(
                        action_type=action_type,
                        target=name,
                        value=path,
                        line_number=line_number
                    )
                
                elif action_type == ActionType.MAESTRO_SCREENSHOT:
                    return TestAction(
                        action_type=action_type,
                        target="maestro_with_analysis",
                        line_number=line_number
                    )
                
                elif action_type == ActionType.ANALYZE:
                    # Check if this is "annotated screenshot" or "call omniparser"
                    if "annotated" in line.lower():
                        return TestAction(
                            action_type=action_type,
                            target="current_screenshot",
                            line_number=line_number
                        )
                    else:
                        target = match.group(1) if match.group(1) else ""
                        return TestAction(
                            action_type=action_type,
                            target=target.strip(),
                            line_number=line_number
                        )
                
                
                elif action_type in [ActionType.FIND, ActionType.TAP, ActionType.CLICK]:
                    # Check if this is a combined find+tap action
                    if action_type == ActionType.FIND and 'tap' in line.lower():
                        target = match.group(1).strip()
                        return TestAction(
                            action_type=ActionType.TAP,
                            target=target,
                            line_number=line_number
                        )
                    
                    target = match.group(1) if match.lastindex else ""
                    return TestAction(
                        action_type=action_type,
                        target=target.strip() if target else "",
                        line_number=line_number
                    )
                
                elif action_type == ActionType.ENTER:
                    return TestAction(
                        action_type=action_type,
                        value=match.group(1).strip(),
                        line_number=line_number
                    )
        
        # If no pattern matches, return None
        return None
    
    def validate_actions(self, actions: List[TestAction]) -> List[str]:
        """Validate the action sequence and return any warnings"""
        warnings = []
        
        # Check for enter without preceding find/tap
        for i, action in enumerate(actions):
            if action.action_type == ActionType.ENTER:
                if i == 0 or actions[i-1].action_type not in [ActionType.FIND, ActionType.TAP, ActionType.CLICK]:
                    warnings.append(
                        f"Line {action.line_number}: ENTER action without preceding FIND/TAP action"
                    )
        
        return warnings
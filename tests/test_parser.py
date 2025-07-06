"""
Unit tests for the test case parser
"""
import unittest
from pathlib import Path
from src.parser import TestCaseParser, ActionType

class TestTestCaseParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = TestCaseParser()
    
    def test_parse_open_action(self):
        """Test parsing of open web application action"""
        action = self.parser._parse_line("open web application https://testsk.unilabs.pro", 1)
        self.assertEqual(action.action_type, ActionType.OPEN)
        self.assertEqual(action.target, "https://testsk.unilabs.pro")
    
    def test_parse_wait_action(self):
        """Test parsing of wait action"""
        action = self.parser._parse_line("wait 5 seconds while splash screen is loading", 1)
        self.assertEqual(action.action_type, ActionType.WAIT)
        self.assertEqual(action.wait_time, 5.0)
    
    def test_parse_screenshot_action(self):
        """Test parsing of screenshot action"""
        action = self.parser._parse_line("take screenshot and call ScreenAPI LLM for analyzing", 1)
        self.assertEqual(action.action_type, ActionType.SCREENSHOT)
    
    def test_parse_find_and_tap_action(self):
        """Test parsing of combined find and tap action"""
        action = self.parser._parse_line("find login text field and tap on it", 1)
        self.assertEqual(action.action_type, ActionType.TAP)
        self.assertEqual(action.target, "login text field")
    
    def test_parse_enter_action(self):
        """Test parsing of enter action"""
        action = self.parser._parse_line("enter here admin@unilabs.sk", 1)
        self.assertEqual(action.action_type, ActionType.ENTER)
        self.assertEqual(action.value, "admin@unilabs.sk")
    
    def test_parse_with_line_numbers(self):
        """Test parsing lines with number prefixes"""
        action = self.parser._parse_line("1- open web application https://example.com", 1)
        self.assertEqual(action.action_type, ActionType.OPEN)
        self.assertEqual(action.target, "https://example.com")
        
        action = self.parser._parse_line("2.5- wait 3 seconds", 1)
        self.assertEqual(action.action_type, ActionType.WAIT)
        self.assertEqual(action.wait_time, 3.0)

if __name__ == '__main__':
    unittest.main()
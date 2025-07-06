#!/usr/bin/env python3
"""
Script called by Maestro to analyze screenshots and update coordinates
"""
import os
import sys
import subprocess
import yaml
from pathlib import Path

def main():
    # Debug: Print all environment variables
    print("=== MAESTRO SCRIPT DEBUG ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script path: {__file__}")
    print(f"Python executable: {sys.executable}")
    print("Environment variables:")
    for key, value in os.environ.items():
        if key.startswith(('SCREENSHOT', 'TEST', 'ACTION')):
            print(f"  {key}={value}")
    
    # Get parameters from environment variables
    screenshot_path = os.getenv('SCREENSHOT_PATH')
    test_name = os.getenv('TEST_NAME') 
    action_index = os.getenv('ACTION_INDEX')
    
    print(f"Parsed values:")
    print(f"  screenshot_path: {screenshot_path}")
    print(f"  test_name: {test_name}")
    print(f"  action_index: {action_index}")
    
    if not all([screenshot_path, test_name, action_index]):
        print("ERROR: Missing required environment variables")
        print("Required: SCREENSHOT_PATH, TEST_NAME, ACTION_INDEX")
        sys.exit(1)
    
    # Check if screenshot file exists
    full_path = Path(screenshot_path)
    if not full_path.exists():
        print(f"ERROR: Screenshot file does not exist: {full_path}")
        print(f"Absolute path: {full_path.absolute()}")
        # List parent directory
        if full_path.parent.exists():
            print(f"Parent directory contents:")
            for item in full_path.parent.iterdir():
                print(f"  {item}")
        sys.exit(1)
    
    print(f"SUCCESS: Found screenshot file: {full_path}")
    print(f"File size: {full_path.stat().st_size} bytes")
    
    # Run OmniParser analysis using the main ScreenAI tool
    try:
        # Call the main ScreenAI script to analyze this specific screenshot
        cmd = [
            sys.executable, 
            "-m", "src.main",
            "--analyze-screenshot", screenshot_path,
            "--update-yaml", f"flows/{test_name}.yaml"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("Screenshot analysis completed successfully")
            print(result.stdout)
        else:
            print(f"Analysis failed: {result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error running analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple runner script for ScreenAI Test Automation Tool
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run main
if __name__ == "__main__":
    from src.main import main
    main()
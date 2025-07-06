#!/usr/bin/env python3
"""
Quick test of the screenshot watcher functionality
"""
import time
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_watcher():
    """Test the watcher by copying an existing screenshot"""
    screenshots_dir = Path("screenshots/objednavka")
    yaml_file = Path("flows/objednavka.yaml")
    
    if not screenshots_dir.exists():
        logger.error(f"Screenshots directory not found: {screenshots_dir}")
        return False
        
    # Find an existing screenshot
    existing_files = list(screenshots_dir.glob("*.png"))
    if not existing_files:
        logger.error("No existing screenshots found to test with")
        return False
    
    source_file = existing_files[0]
    test_file = screenshots_dir / f"test_screenshot_{int(time.time())}.png"
    
    logger.info(f"🧪 Testing watcher by copying: {source_file.name}")
    logger.info(f"📋 Creating test file: {test_file.name}")
    
    # Copy file to trigger watcher
    shutil.copy2(source_file, test_file)
    
    logger.info("✅ Test file created")
    logger.info("🔍 Watcher should detect this file if running...")
    logger.info(f"🗑️  Clean up: rm {test_file}")
    
    # Clean up after 5 seconds
    time.sleep(5)
    if test_file.exists():
        test_file.unlink()
        logger.info("🧹 Test file cleaned up")
    
    return True

if __name__ == "__main__":
    test_watcher()
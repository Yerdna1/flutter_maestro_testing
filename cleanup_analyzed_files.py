#!/usr/bin/env python3
"""
Cleanup script to move existing analyzed files to FINISHED folder
"""
import logging
from pathlib import Path
import shutil

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def cleanup_analyzed_files():
    """Move all existing analyzed files to FINISHED folder"""
    screenshots_dir = Path("screenshots/objednavka")
    
    if not screenshots_dir.exists():
        logger.error(f"Screenshots directory not found: {screenshots_dir}")
        return
    
    # Create FINISHED folder if it doesn't exist
    finished_dir = screenshots_dir / "FINISHED"
    finished_dir.mkdir(exist_ok=True)
    
    # Find all analyzed files
    analyzed_files = list(screenshots_dir.glob("*_analyzed*"))
    
    if not analyzed_files:
        logger.info("No analyzed files found to clean up")
        return
    
    logger.info(f"Found {len(analyzed_files)} analyzed files to move")
    
    moved_count = 0
    for analyzed_file in analyzed_files:
        try:
            dest_path = finished_dir / analyzed_file.name
            if not dest_path.exists():
                shutil.move(str(analyzed_file), str(dest_path))
                logger.info(f"📁 Moved: {analyzed_file.name}")
                moved_count += 1
            else:
                logger.warning(f"⚠️  File already exists in FINISHED: {analyzed_file.name}")
                # Remove the duplicate
                analyzed_file.unlink()
                logger.info(f"🗑️  Removed duplicate: {analyzed_file.name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to move {analyzed_file.name}: {e}")
    
    logger.info(f"✅ Cleanup complete! Moved {moved_count} files to FINISHED folder")

if __name__ == "__main__":
    cleanup_analyzed_files()
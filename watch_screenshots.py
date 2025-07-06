#!/usr/bin/env python3
"""
Screenshot Watcher - Automatically updates YAML coordinates when new screenshots are created
"""
import time
import logging
from pathlib import Path
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ScreenshotHandler(FileSystemEventHandler):
    """Handles new screenshot files and updates coordinates"""
    
    def __init__(self, yaml_file: Path):
        self.yaml_file = yaml_file
        self.processed_files = set()
        
    def on_created(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if self.should_process_file(file_path):
            logger.info(f"🖼️  New screenshot detected: {file_path.name}")
            self.update_coordinates(file_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if self.should_process_file(file_path):
            logger.info(f"🔄 Screenshot modified: {file_path.name}")
            self.update_coordinates(file_path)
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed"""
        return (file_path.suffix == '.png' and 
                'objednavka' in file_path.name and 
                str(file_path) not in self.processed_files and
                '_analyzed' not in file_path.name and  # Skip any analyzed files
                not file_path.name.startswith('.'))
    
    def process_existing_files(self, screenshots_dir: Path):
        """Process any existing screenshot files"""
        existing_files = list(screenshots_dir.glob("*objednavka*.png"))
        # Filter out analyzed files and only get original screenshots
        filtered_files = [f for f in existing_files if self.should_process_file(f)]
        # Only process the most recent files to avoid overwhelming the system
        recent_files = sorted(filtered_files, key=lambda f: f.stat().st_mtime)[-3:]
        
        if recent_files:
            logger.info(f"📁 Processing {len(recent_files)} recent existing screenshots...")
            for file_path in recent_files:
                logger.info(f"🔍 Processing existing: {file_path.name}")
                self.update_coordinates(file_path)
    
    def update_coordinates(self, screenshot_path: Path):
        """Update YAML coordinates for the new screenshot"""
        # Mark as processed to avoid duplicate processing
        self.processed_files.add(str(screenshot_path))
        
        try:
            logger.info(f"🔍 Analyzing screenshot: {screenshot_path}")
            
            # Run coordinate analysis
            cmd = [
                sys.executable,
                "-m", "src.main",
                "--analyze-screenshot", str(screenshot_path),
                "--update-yaml", str(self.yaml_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Updated coordinates in {self.yaml_file.name}")
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-3:]:  # Show last 3 lines of output
                        if line.strip():
                            logger.info(f"   {line.strip()}")
                
                # Move analyzed files to FINISHED folder
                self._move_analyzed_files_to_finished(screenshot_path)
            else:
                logger.error(f"❌ Analysis failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ Analysis timed out")
        except Exception as e:
            logger.error(f"💥 Error updating coordinates: {e}")
    
    def _move_analyzed_files_to_finished(self, original_screenshot: Path):
        """Move analyzed files to FINISHED folder"""
        try:
            # Create FINISHED folder if it doesn't exist
            finished_dir = original_screenshot.parent / "FINISHED"
            finished_dir.mkdir(exist_ok=True)
            
            # Find all related analyzed files
            base_name = original_screenshot.stem  # filename without extension
            screenshot_dir = original_screenshot.parent
            
            analyzed_files = list(screenshot_dir.glob(f"{base_name}_analyzed*"))
            
            for analyzed_file in analyzed_files:
                if analyzed_file.exists():
                    dest_path = finished_dir / analyzed_file.name
                    analyzed_file.rename(dest_path)
                    logger.info(f"📁 Moved to FINISHED: {analyzed_file.name}")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to move analyzed files: {e}")

def main():
    """Main entry point"""
    screenshots_dir = Path("screenshots/objednavka")
    yaml_file = Path("flows/objednavka.yaml")
    
    if not screenshots_dir.exists():
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    if not yaml_file.exists():
        logger.error(f"YAML file not found: {yaml_file}")
        sys.exit(1)
    
    logger.info(f"👀 Watching for screenshots in: {screenshots_dir}")
    logger.info(f"📄 Will update coordinates in: {yaml_file}")
    
    # Set up file watcher
    event_handler = ScreenshotHandler(yaml_file)
    
    # Process existing files first
    event_handler.process_existing_files(screenshots_dir)
    
    logger.info("🚀 Start your Maestro test now!")
    logger.info("📝 Press Ctrl+C to stop watching")
    
    observer = Observer()
    observer.schedule(event_handler, str(screenshots_dir), recursive=False)
    
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Stopping screenshot watcher...")
        observer.stop()
    
    observer.join()
    logger.info("👋 Screenshot watcher stopped")

if __name__ == "__main__":
    main()
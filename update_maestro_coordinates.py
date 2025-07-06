#!/usr/bin/env python3
"""
Post-Maestro Coordinate Updater - Updates all TODO coordinates from Maestro screenshots
"""
import argparse
import logging
from pathlib import Path
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def update_coordinates_from_screenshots(screenshots_dir: Path, yaml_file: Path):
    """Update YAML coordinates from all screenshots in directory"""
    
    if not screenshots_dir.exists():
        logger.error(f"Screenshots directory not found: {screenshots_dir}")
        return False
        
    if not yaml_file.exists():
        logger.error(f"YAML file not found: {yaml_file}")
        return False
    
    # Find all screenshot files
    screenshot_files = sorted(screenshots_dir.glob("*.png"))
    
    if not screenshot_files:
        logger.warning(f"No PNG files found in {screenshots_dir}")
        return False
    
    logger.info(f"Found {len(screenshot_files)} screenshots to process")
    
    # Process each screenshot
    updated_count = 0
    for screenshot_path in screenshot_files:
        logger.info(f"🔍 Processing: {screenshot_path.name}")
        
        try:
            # Run coordinate analysis
            cmd = [
                sys.executable,
                "-m", "src.main", 
                "--analyze-screenshot", str(screenshot_path),
                "--update-yaml", str(yaml_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Updated coordinates from {screenshot_path.name}")
                updated_count += 1
            else:
                logger.warning(f"⚠️  Analysis failed for {screenshot_path.name}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Analysis timed out for {screenshot_path.name}")
        except Exception as e:
            logger.error(f"💥 Error processing {screenshot_path.name}: {e}")
    
    logger.info(f"🎯 Successfully updated coordinates from {updated_count}/{len(screenshot_files)} screenshots")
    return updated_count > 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Update Maestro YAML coordinates from screenshots')
    parser.add_argument('--screenshots', '-s', type=Path, 
                       default=Path('screenshots/objednavka'),
                       help='Directory containing Maestro screenshots')
    parser.add_argument('--yaml', '-y', type=Path,
                       default=Path('flows/objednavka.yaml'),
                       help='YAML file to update')
    
    args = parser.parse_args()
    
    logger.info("🔧 Maestro Coordinate Updater")
    logger.info(f"📁 Screenshots: {args.screenshots}")
    logger.info(f"📄 YAML file: {args.yaml}")
    logger.info("")
    
    success = update_coordinates_from_screenshots(args.screenshots, args.yaml)
    
    if success:
        logger.info("✅ Coordinate update completed!")
        logger.info(f"📝 Updated YAML: {args.yaml}")
        logger.info("🚀 You can now re-run Maestro with updated coordinates")
    else:
        logger.error("❌ Coordinate update failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
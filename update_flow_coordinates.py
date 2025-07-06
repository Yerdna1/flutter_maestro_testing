#!/usr/bin/env python3
"""
Flow Coordinate Updater - Analyzes screenshots and updates Maestro flow coordinates
"""
import argparse
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.coordinate_updater import FlowCoordinateUpdater
from src.vision import VisionAnalyzer
from src.matcher import UIElementMatcher

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def analyze_screenshots_and_update_flow(screenshot_dir: Path, main_flow_path: Path):
    """
    Analyze all screenshots in directory and update main flow coordinates
    
    Args:
        screenshot_dir: Directory containing screenshots to analyze
        main_flow_path: Path to main flow YAML file to update
    """
    if not screenshot_dir.exists():
        logger.error(f"Screenshot directory not found: {screenshot_dir}")
        return False
    
    if not main_flow_path.exists():
        logger.error(f"Main flow file not found: {main_flow_path}")
        return False
    
    # Initialize components
    vision_analyzer = VisionAnalyzer()
    updater = FlowCoordinateUpdater()
    
    # Find screenshot files
    screenshot_files = list(screenshot_dir.glob("*.png"))
    if not screenshot_files:
        logger.error(f"No PNG files found in {screenshot_dir}")
        return False
    
    logger.info(f"Found {len(screenshot_files)} screenshots to analyze")
    
    # Analyze each screenshot
    screenshot_results = {}
    for screenshot_path in screenshot_files:
        try:
            logger.info(f"Analyzing {screenshot_path.name}...")
            
            # Analyze screenshot with OmniParser
            elements = vision_analyzer.analyze_image(str(screenshot_path))
            
            if elements:
                screenshot_results[str(screenshot_path)] = elements
                logger.info(f"Found {len(elements)} elements in {screenshot_path.name}")
            else:
                logger.warning(f"No elements detected in {screenshot_path.name}")
                
        except Exception as e:
            logger.error(f"Error analyzing {screenshot_path}: {e}")
            continue
    
    if not screenshot_results:
        logger.error("No valid analysis results found")
        return False
    
    # Update main flow with coordinates
    try:
        updater.analyze_and_update_flow(screenshot_results, main_flow_path)
        logger.info("✅ Flow coordinates updated successfully!")
        return True
    except Exception as e:
        logger.error(f"Error updating flow coordinates: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Update Maestro flow coordinates from screenshot analysis')
    parser.add_argument('--screenshots', '-s', type=Path, 
                       default=Path('screenshots/objednavka'),
                       help='Directory containing screenshots to analyze')
    parser.add_argument('--flow', '-f', type=Path,
                       default=Path('flows/objednavka_main.yaml'),
                       help='Main flow file to update')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🔍 Starting flow coordinate analysis and update...")
    logger.info(f"📁 Screenshot directory: {args.screenshots}")
    logger.info(f"📄 Main flow file: {args.flow}")
    
    success = analyze_screenshots_and_update_flow(args.screenshots, args.flow)
    
    if success:
        logger.info("\n✅ Coordinate update completed successfully!")
        logger.info("🚀 You can now run: maestro test flows/objednavka_main.yaml")
    else:
        logger.error("\n❌ Coordinate update failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
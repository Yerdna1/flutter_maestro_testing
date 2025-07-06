#!/usr/bin/env python3
"""
Run testCase1 Maestro flow, take screenshot, then continue with objednavka analysis
"""
import subprocess
import time
import logging
from pathlib import Path
from src.main import ScreenAIOrchestrator
from src.screenshot import ScreenshotCapture
from src.vision import OmniParserVision

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_maestro_and_continue():
    """Run testCase1 flow in Maestro, then continue with objednavka analysis"""
    
    try:
        # Step 1: Run testCase1.yaml in Maestro (includes screenshot steps)
        logger.info("Running testCase1.yaml in Maestro...")
        result = subprocess.run([
            'maestro', 'test', 'flows/testCase1.yaml'
        ], capture_output=True, text=True, cwd='/Volumes/DATA/Python/ScreenAI')
        
        if result.returncode != 0:
            logger.error(f"Maestro test failed: {result.stderr}")
            return
        
        logger.info("Maestro test completed successfully")
        
        # Step 2: Maestro has completed with screenshot steps included
        logger.info("Maestro flow completed with screenshot steps")
        
        # Step 3: Use the post-login screenshot from testCase1 execution (step_02.png)
        logger.info("Using post-login screenshot from testCase1 execution...")
        post_login_screenshot = "screenshots/step_02.png"
        
        if not Path(post_login_screenshot).exists():
            logger.error(f"Post-login screenshot not found: {post_login_screenshot}")
            return
            
        vision = OmniParserVision()
        elements = vision.detect_elements(post_login_screenshot)
        
        # Save annotated image for objednavka analysis
        annotated_path = post_login_screenshot.replace('.png', '_objednavka_analysis.png')
        vision.save_annotated_image(post_login_screenshot, elements, annotated_path)
        logger.info(f"Found {len(elements)} UI elements in post-login state for objednavka")
        
        screenshot_path = post_login_screenshot
        dimensions = (3488, 1912)  # Use dimensions from step_02.png
        
        # Step 4: Process objednavka test case starting with this screenshot
        logger.info("Processing objednavka.txt with post-login analysis...")
        orchestrator = ScreenAIOrchestrator(debug=False, continue_session=True)
        
        # Manually set up the initial state
        screenshot_capture = ScreenshotCapture()
        orchestrator.screenshot = screenshot_capture
        orchestrator.screenshot_counter = 1
        orchestrator.detected_elements = {0: elements}  # Screenshot at action 0
        orchestrator.image_dimensions = {0: dimensions}
        orchestrator.current_elements = elements
        orchestrator.current_screenshot_action = 0
        
        # Process objednavka test case
        test_path = Path("test_cases/objednavka.txt")
        flow_file = orchestrator.process_test_case(test_path)
        logger.info(f"Generated objednavka flow: {flow_file}")
        
        # Step 5: Combine flows
        logger.info("Combining testCase1 and objednavka flows...")
        combine_flows()
        
        logger.info("Complete workflow finished successfully!")
        
    except Exception as e:
        logger.error(f"Error in maestro workflow: {e}")
        raise

def combine_flows():
    """Combine testCase1.yaml and objednavka.yaml into one complete flow"""
    
    # Read testCase1.yaml
    testcase1_path = Path("flows/testCase1.yaml")
    objednavka_path = Path("flows/objednavka.yaml") 
    combined_path = Path("flows/complete_flow.yaml")
    
    with open(testcase1_path, 'r') as f:
        testcase1_content = f.read()
    
    with open(objednavka_path, 'r') as f:
        objednavka_content = f.read()
    
    # Extract steps from objednavka (skip the header)
    objednavka_lines = objednavka_content.split('\n')
    objednavka_steps = []
    skip_header = True
    
    for line in objednavka_lines:
        if line.strip().startswith('- '):
            skip_header = False
        if not skip_header and line.strip():
            objednavka_steps.append(line)
    
    # Combine flows
    combined_content = testcase1_content.rstrip()
    if objednavka_steps:
        combined_content += '\n# Continue with order functionality\n'
        combined_content += '\n'.join(objednavka_steps)
    
    # Write combined flow
    with open(combined_path, 'w') as f:
        f.write(combined_content)
    
    logger.info(f"Combined flow saved: {combined_path}")

if __name__ == "__main__":
    run_maestro_and_continue()
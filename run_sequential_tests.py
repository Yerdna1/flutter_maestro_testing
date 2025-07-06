#!/usr/bin/env python3
"""
Sequential test runner for testCase1 followed by objednavka
"""
import logging
from pathlib import Path
from src.main import ScreenAIOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_sequential_tests():
    """Run testCase1 followed by objednavka in the same browser session"""
    
    # Initialize orchestrator (no context manager to keep browser open)
    orchestrator = ScreenAIOrchestrator(debug=False, continue_session=False)
    
    try:
        # Run testCase1 first
        logger.info("Running testCase1.txt...")
        test1_path = Path("test_cases/testCase1.txt")
        flow1 = orchestrator.process_test_case(test1_path)
        logger.info(f"Generated flow: {flow1}")
        
        # Now switch to continue mode for objednavka
        orchestrator.continue_session = True
        logger.info("Running objednavka.txt...")
        test2_path = Path("test_cases/objednavka.txt")
        flow2 = orchestrator.process_test_case(test2_path)
        logger.info(f"Generated flow: {flow2}")
        
        logger.info("Sequential tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error running sequential tests: {e}")
        raise
    finally:
        # Clean up
        orchestrator.cleanup()

if __name__ == "__main__":
    run_sequential_tests()
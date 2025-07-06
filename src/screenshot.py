"""
Screenshot capture module for web applications using Selenium
"""
import time
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ScreenshotCapture:
    """Handles screenshot capture for web applications"""
    
    def __init__(self, headless: bool = False, screenshot_dir: str = "screenshots"):
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(exist_ok=True)
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with options"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # Disable images for faster loading (optional)
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # options.add_experimental_option("prefs", prefs)
        
        try:
            # Try using webdriver-manager first
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            logger.warning(f"WebDriver Manager failed: {e}, trying system chromedriver")
            # Fallback to system chromedriver
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
        
        self.driver.maximize_window()
    
    def open_url(self, url: str, wait_time: float = 2.0):
        """Open a URL and wait for it to load"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Opening URL: {url}")
        self.driver.get(url)
        time.sleep(wait_time)
    
    def wait(self, seconds: float):
        """Wait for specified seconds"""
        logger.info(f"Waiting for {seconds} seconds")
        time.sleep(seconds)
    
    def take_screenshot(self, name: Optional[str] = None) -> Tuple[str, Tuple[int, int]]:
        """
        Take a screenshot and return the file path and dimensions
        
        Returns:
            Tuple[str, Tuple[int, int]]: (file_path, (width, height))
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"screenshot_{timestamp}"
        
        if not name.endswith('.png'):
            name += '.png'
        
        file_path = self.screenshot_dir / name
        
        # Take screenshot
        self.driver.save_screenshot(str(file_path))
        logger.info(f"Screenshot saved: {file_path}")
        
        # Get dimensions
        image = Image.open(file_path)
        dimensions = image.size
        
        return str(file_path), dimensions
    
    def get_current_url(self) -> str:
        """Get the current URL"""
        return self.driver.current_url
    
    def get_page_title(self) -> str:
        """Get the current page title"""
        return self.driver.title
    
    def wait_for_element(self, timeout: float = 10.0):
        """Wait for page to be ready"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            logger.warning(f"Timeout waiting for page ready: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
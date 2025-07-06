"""
Colored logging utility for ScreenAI
"""
import logging
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    # Color mappings for different log levels
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE,
    }
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
    
    def format(self, record):
        # Get the color for this log level
        log_color = self.COLORS.get(record.levelname, '')
        
        # Add color to the log level
        colored_levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        
        # Special handling for specific messages
        message = record.getMessage()
        
        # Color specific message types
        if "Screenshot" in message and "saved" in message:
            message = f"{Fore.CYAN}{message}{Style.RESET_ALL}"
        elif "Detected" in message and "elements" in message:
            message = f"{Fore.MAGENTA}{message}{Style.RESET_ALL}"
        elif "Found" in message and "UI elements" in message:
            message = f"{Fore.MAGENTA}{message}{Style.RESET_ALL}"
        elif "Processing action" in message:
            message = f"{Fore.BLUE}{message}{Style.RESET_ALL}"
        elif "No element found" in message or "No match found" in message:
            message = f"{Fore.YELLOW}{message}{Style.RESET_ALL}"
        elif "Speed:" in message:
            message = f"{Fore.CYAN}{message}{Style.RESET_ALL}"
        elif "icons," in message:
            message = f"{Fore.MAGENTA}{message}{Style.RESET_ALL}"
        
        # Create a new record with colored levelname
        record.levelname = colored_levelname
        record.msg = message
        
        return super().format(record)

def setup_colored_logging(level=logging.INFO, debug=False):
    """Setup colored logging for the application"""
    
    if debug:
        level = logging.DEBUG
    
    # Create formatter
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger
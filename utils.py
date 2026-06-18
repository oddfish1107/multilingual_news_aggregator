import time
import logging
from functools import wraps

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def timing_decorator(func):
    """Decorator to measure and log the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting {func.__name__}...")
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Finished {func.__name__} in {end_time - start_time:.4f} seconds.")
        return result
    return wrapper

def logging_decorator(func):
    """Decorator to log function calls and their execution status."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Executing {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} executed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

def filter_text(text: str) -> str:
    """Filters text using lambda functions for cleaning."""
    if not text:
        return ""
    # Lambda for text filtering: remove extra spaces, tabs, and newlines
    cleaner = lambda t: ' '.join(t.split())
    return cleaner(text)

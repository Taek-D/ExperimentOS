import time
import functools
import logging
import random
from typing import Tuple, Type
import httpx

logger = logging.getLogger(__name__)

def retry_request(
    max_retries: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)
):
    """
    Decorator to retry a function (usually an API request) on failure.
    Retries on:
    - httpx.HTTPStatusError with status codes in retryable_status_codes
    - httpx.RequestError (connection issues, timeouts)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in retryable_status_codes:
                        last_exception = e
                        logger.warning(
                            f"Request failed (Attempt {attempt + 1}/{max_retries + 1}) "
                            f"Status: {e.response.status_code}. Retrying in {delay:.2f}s..."
                        )
                    else:
                        raise e
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    last_exception = e
                    logger.warning(
                        f"Request failed (Attempt {attempt + 1}/{max_retries + 1}) "
                        f"Error: {e}. Retrying in {delay:.2f}s..."
                    )
                
                if attempt < max_retries:
                    # Add jitter
                    sleep_time = delay * (0.5 + random.random())
                    time.sleep(sleep_time)
                    delay *= backoff_factor
            
            if last_exception:
                logger.error(f"Max retries reached. Last error: {last_exception}")
                raise last_exception
        return wrapper
    return decorator

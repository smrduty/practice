from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from  playwright.async_api import TimeoutError as PlaywrightTimeoutError
import asyncio

def playwright_retry():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=0.5, min=0.5, max=5
        ),
        retry=retry_if_exception_type((
            PlaywrightTimeoutError,
            asyncio.TimeoutError,
        )),
        reraise=True,
    )



from logger import logger

async def auto_scroll(page, scroll_times: int = 5, pause: int = 1000):
    logger.info(f"Starting scrolling: {scroll_times} times")

    for i in range(scroll_times):
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(pause)
        logger.debug(f"Scroll {i+1}/{scroll_times}")

    logger.info("Scrolling ended")




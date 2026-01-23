import asyncio
from typing import Optional

from playwright.async_api import async_playwright, Locator

from config import config
from logger import logger
from utils.retry import playwright_retry

# Ограничение параллельных карточек
semaphore = asyncio.Semaphore(5)


class BaseParser:
    def __init__(self):
        self.browser = None
        self.page = None

    async def start(self):
        logger.info("Browser starting...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=config["HEADLESS"],
            slow_mo=50,
            args=[
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await self.browser.new_context(
            storage_state="avito_state.json",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="ru-RU",
        )

        self.page = await context.new_page()

    async def stop(self):
        logger.info("Closing browser...")
        await self.browser.close()
        await self.playwright.stop()

    @playwright_retry()
    async def safe_text(self, locator: Locator) -> Optional[str]:
        el = locator.first
        if await el.count() == 0:
            return None
        text = await el.text_content()
        return text.strip() if text else None

    async def run_with_semaphore(self, coro):
        async with semaphore:
            return await coro

    async def parse(self, *args, **kwargs):
        raise NotImplementedError("parse() must be implemented in child class")




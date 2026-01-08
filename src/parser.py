from playwright.async_api import async_playwright
from playwright.async_api import Locator
from typing import TypedDict, Optional
from dataclasses import dataclass
import asyncio

from config import BASE_URL, HEADLESS, SCROLL_TIMES, SCROLL_PAUSE
from logger import logger
from utils import auto_scroll
from models import Vacancy

import selectors

semaphore = asyncio.Semaphore(5)

async def safe_text(locator: Locator) -> Optional[str]:
        return (await locator.text_content()).strip() if await locator.count() else None

async def parse_card(card: Locator) -> Vacancy:
    address = await safe_text(card.locator(selectors.VACANCY_ADDRESS))
    address_additional = await safe_text(card.locator(selectors.VACANCY_ADDRESS_ADDITIONAL))
    complete_address = " ".join(filter(None, [address, address_additional]))
    return Vacancy(
        title=await safe_text(card.locator(selectors.VACANCY_TITLE)),
        salary=await safe_text(card.locator(selectors.VACANCY_SALARY)),
        experience=await safe_text(card.locator(selectors.VACANCY_EXPERIENCE)),
        address=complete_address,
        url=await card.locator(selectors.VACANCY_URL).get_attribute("href")
    )

async def parse_card_limited(card: Locator) -> Vacancy:
    async with semaphore:
        return await parse_card(card)


async def parse_items(query: str, max_pages: int):
    #semaphore = asyncio.Semaphore(5)
    results = []
    logger.info("Starting parser...")
    logger.info(f"Searching query: {query}")

    async with async_playwright() as p:
        logger.info("Browser starting...")
        browser = await p.chromium.launch(headless=HEADLESS, slow_mo=50)
        page = await browser.new_page()

        logger.info("Following link...")
        await page.goto(BASE_URL, timeout=60_000)

        logger.info("Entering a query...")
        await page.fill(selectors.SEARCH_INPUT, query)
        await page.keyboard.press("Enter")

        await page.keyboard.press("Escape")

        #logger.info("Waiting for vacancies...")
        for page_number in range(max_pages):
            
            logger.info(f"Page number {page_number + 1}")

            try:
                await page.wait_for_selector(selectors.VACANCY_CARD)
            except Exception:
                logger.exception("No vacancies loaded")
                return results
            
            await auto_scroll(page, SCROLL_TIMES, SCROLL_PAUSE)
            
            cards = page.locator(selectors.VACANCY_CARD)
            count = await cards.count()
            logger.info(f"Vacancies found: {count}")
            
            tasks = [
                parse_card_limited(cards.nth(i))
                for i in range(count)
            ]
            page_results = await asyncio.gather(*tasks)
            results.extend(page_results)

            next_page_button = page.locator(selectors.NEXT_PAGE_BUTTON)
            if await next_page_button.count() == 0:
                logger.info("NO next page button")
                break

            await next_page_button.click()
            #await page.wait_for_load_state("networkidle", timeout=30000)

        logger.info("Closing browser...")
        await browser.close()

    logger.info("Ending parser...")
    return results


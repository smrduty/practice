import asyncio
from typing import Optional

from playwright.async_api import Locator

from logger import logger
from utils.scroll import auto_scroll
from models import Vacancy

from base_parser import BaseParser
import selectors
from config import config

import re

class AVITOParser(BaseParser):

    def make_full_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        if url.startswith("http"):
            return url
        return f"https://avito.ru{url}"

    async def select_region(self, region: str):
        location_button = self.page.locator(".buyer-pages-mfe-location-nev1ty")
        location_popup = self.page.locator("[data-marker='popup-location/popup']")

        MAX_ATTEMPTS = 10

        for attempt in range(MAX_ATTEMPTS):
            if await location_popup.count() > 0:
                break
            
            logger.info(f"Opening location popup (attempt {attempt + 1})")

            await self.page.wait_for_timeout(1000)
            await location_button.click()

        await location_popup.wait_for(state='visible', timeout=60_000)

        # await self.page.evaluate("""
        #     document.querySelector('.buyer-pages-mfe-location-nev1ty')?.click()
        # """)

        # await self.page.locator("[data-marker='popup-location/popup']").wait_for(
        #     state="visible",
        #     timeout=60_000
        # )

        region_input = self.page.locator('[data-marker="popup-location/region"] input')
        # await region_input.click()
        # await region_input.type(region, delay=50)
        await region_input.fill(region)

        default_region = self.page.get_by_role(
            'checkbox',
            name="Все регионы"
        )
        
        pattern = re.compile(
            rf"^{re.escape(region)}(,|$)",
            re.IGNORECASE
        )

        target_region = self.page.locator('[role="checkbox"]').filter(
            has_text=pattern
        )

        await target_region.wait_for(state="visible", timeout=10_000)
        await target_region.click()
        confirm_region = self.page.locator("[data-marker='popup-location/save-button']")
        await confirm_region.click()
    
    async def fill_query(self, query: str):
        query_input = self.page.locator('[data-marker="search-form/suggest/input"]')
        await query_input.fill(query)
        await self.page.keyboard.press("Enter")

    async def fill_salary_from(self, salary_from: str):
        salary_from_element = self.page.locator('[marker="price-from"]')
        await salary_from_element.fill(salary_from)
        submit_button = self.page.locator('[data-marker="search-filters/submit-button"]')
        await submit_button.click()

    async def extract_experience(self, card: Locator):
        locator_full = card.locator('[data-marker="item-specific-params"]')

        if await locator_full.count() == 0:
            return None
    
        text = await locator_full.first.inner_text()
        parts = [p.strip() for p in text.split('·')]
        return parts[2] if len(parts) == 3 else None

    async def parse_card(self, card: Locator):
        url = await card.locator('[itemprop="url"]').first.get_attribute("href")
        title = await card.locator('[itemprop="url"]').nth(1).get_attribute("title")
        salary_locator = card.locator('[data-marker="item-price"] span')
        salary = await salary_locator.inner_text()
        experience = await self.extract_experience(card)
        location = await card.locator('[data-marker="item-location"]').inner_text()
        return Vacancy(
            title=title,
            salary=salary,
            experience=experience,
            address=location,
            url=self.make_full_url(url)
        )
    
    async def parse(self, query: str, max_pages: int, region: str, salary_from: str):
        results = []

        logger.info("Starting AVITO parser...")
        logger.info(f"Searching query: {query}")

        await self.start()

        logger.info(f"Following link...")
        await self.page.goto(config["BASE_URL_AVITO"], timeout=60_000)

        #await self.page.wait_for_load_state("networkidle")

        logger.info(f"Entering region...")
        await self.select_region(region)

        logger.info(f"Entering query...")
        await self.fill_query(query)
        
        logger.info(f"Filling salary from...")
        await self.fill_salary_from(salary_from)

        for page_number in range(max_pages):
            logger.info(f"Page number {page_number + 1}")

            try:
                await self.page.wait_for_selector('[data-marker="item"]')
            except Exception:
                logger.exception("No vacancies loaded")
                
            await auto_scroll(self.page, config["SCROLL_TIMES"], config["SCROLL_PAUSE"])

            cards = self.page.locator('[data-marker="item"]')
            cards_count = await cards.count()
            logger.info(f"Vacancies found: {cards_count}")

            tasks = [
                self.run_with_semaphore(
                    self.parse_card(cards.nth(i))
                )
                for i in range(cards_count)
            ]

            page_results = await asyncio.gather(*tasks)
            results.extend(page_results)

            next_page_button = self.page.locator('[data-marker="pagination-button/nextPage"]')

            if await next_page_button.count() > 0:
                await next_page_button.click()
            else:
                logger.info("Last page reached")
                break

        await self.stop()
        return results
    







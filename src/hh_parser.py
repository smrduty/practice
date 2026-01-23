import asyncio
from typing import Optional

from playwright.async_api import Locator

from logger import logger
from utils.scroll import auto_scroll
from models import Vacancy

from base_parser import BaseParser
import selectors
from config import config


class HHParser(BaseParser):

    def make_full_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        if url.startswith("http"):
            return url
        return f"https://hh.ru{url}"

    async def specify_salary_from(self, salary: str):
        salary_form = self.page.locator(selectors.SALARY_FORM)
        await salary_form.fill(salary)
        await self.page.keyboard.press("Enter")

    async def select_region(self, region: str):
        region_card = self.page.locator(selectors.REGION_CARD)
        region_card_el = await region_card.element_handle()

        all_regions_count = await region_card.locator(selectors.FIT_REGIONS).count()
        show_all = region_card.locator(selectors.SHOW_ALL_REGIONS_BUTTON)

        MAX_ATTEMPTS = 10

        for attempt in range(MAX_ATTEMPTS):
            if await region_card.locator(selectors.FIT_REGIONS).count() > all_regions_count:
                break
            
            logger.info(f"Opening all selecting regions (attempt {attempt + 1})")

            await show_all.click()
            await self.page.wait_for_timeout(1000)

        await region_card.get_by_label(
            selectors.SEARCH_REGION_LABEL
        ).fill(region)

        await self.page.wait_for_function(
            """(args) => {
                const { root, selector, prev } = args;
                return root.querySelectorAll(selector).length < prev;
            }""",
            arg={
                "root": region_card_el,
                "selector": selectors.FIT_REGIONS,
                "prev": all_regions_count
            }
        )

        fit_regions = region_card.locator(selectors.FIT_REGIONS)
        if await fit_regions.count() == 0:
            logger.warning("Entered region is missing...")
            return None

        await fit_regions.first.check()
        return True

    async def parse_card(self, card: Locator) -> Vacancy:
        address = await self.safe_text(
            card.locator(selectors.VACANCY_ADDRESS)
        )
        address_additional = await self.safe_text(
            card.locator(selectors.VACANCY_ADDRESS_ADDITIONAL)
        )

        complete_address = " ".join(
            filter(None, [address, address_additional])
        )

        url = await card.locator(selectors.VACANCY_URL).get_attribute("href")

        return Vacancy(
            title=await self.safe_text(card.locator(selectors.VACANCY_TITLE)),
            salary=await self.safe_text(card.locator(selectors.VACANCY_SALARY)),
            experience=await self.safe_text(card.locator(selectors.VACANCY_EXPERIENCE)),
            address=complete_address,
            url=self.make_full_url(url)
        )

    async def parse(self, query: str, max_pages: int, region: str, salary_from: str):
        results = []

        logger.info("Starting HH parser...")
        logger.info(f"Searching query: {query}")

        await self.start()

        logger.info("Following link...")
        await self.page.goto(config["BASE_URL_HHRU"], timeout=60_000)

        logger.info("Entering a query...")
        await self.page.fill(selectors.SEARCH_INPUT, query)
        await self.page.keyboard.press("Enter")

        await self.select_region(region)
        await self.specify_salary_from(salary_from)

        for page_number in range(max_pages):
            logger.info(f"Page number {page_number + 1}")

            try:
                await self.page.wait_for_selector(selectors.VACANCY_CARD)
            except Exception:
                logger.exception("No vacancies loaded")
                break

            await auto_scroll(
                self.page,
                config["SCROLL_TIMES"],
                config["SCROLL_PAUSE"]
            )

            cards = self.page.locator(selectors.VACANCY_CARD)
            count = await cards.count()
            logger.info(f"Vacancies found: {count}")

            tasks = [
                self.run_with_semaphore(
                    self.parse_card(cards.nth(i))
                )
                for i in range(count)
            ]

            page_results = await asyncio.gather(*tasks)
            results.extend(page_results)

            next_page_button = self.page.locator(selectors.NEXT_PAGE_BUTTON)
            if await next_page_button.count() > 0:
                await next_page_button.click()
                continue

            page_buttons = self.page.locator(selectors.PAGER_PAGE)
            if await page_buttons.count() == 0:
                logger.info("NO pagination controls found – ending pagination")
                break

            current_button = self.page.locator(
                f"{selectors.PAGER_PAGE}[aria-current='true']"
            )

            if await current_button.count() == 0:
                current_index = 0
            else:
                text = await current_button.first.text_content()
                try:
                    current_index = int(text.strip()) - 1
                except Exception:
                    current_index = 0

            next_index = current_index + 1
            if next_index < await page_buttons.count():
                await page_buttons.nth(next_index).click()
            else:
                logger.info("Reached last pagination button – ending pagination")
                break

        await self.stop()
        logger.info("Ending HH parser...")
        return results


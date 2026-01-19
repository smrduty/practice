from playwright.async_api import async_playwright
from playwright.async_api import Locator
from typing import TypedDict, Optional
from dataclasses import dataclass
import asyncio

from config import config
from logger import logger
from utils.scroll import auto_scroll
from utils.retry import playwright_retry
from models import Vacancy

import selectors

semaphore = asyncio.Semaphore(5)


@playwright_retry()
async def safe_text(locator: Locator) -> Optional[str]:
        #return (await locator.text_content()).strip() if await locator.count() else None
        el = locator.first
        if await el.count() == 0:
            return None
        text = await el.text_content()
        return text.strip() if text else None


@playwright_retry()
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
#мб вынести выбор региона в фильтрах в функцию ниже

async def specify_salary_from(page, salary: str):

    salary_form = page.locator(selectors.SALARY_FORM)
    await salary_form.fill(salary)
    await page.keyboard.press("Enter")

async def select_region(page, region: str):
    
    region_card = page.locator(selectors.REGION_CARD)
    region_card_el = await region_card.element_handle()
    show_all =  region_card.locator(selectors.SHOW_ALL_REGIONS_BUTTON)
    
    #await show_all.focus()
    await show_all.wait_for(state="visible")
    await show_all.wait_for(state="attached")
    await show_all.click()
    
    all_regions_count = await region_card.locator(selectors.FIT_REGIONS).count()
    await region_card.get_by_label(selectors.SEARCH_REGION_LABEL).fill(region)
    
    await page.wait_for_function(
        """(args) => {
            const { root, selector, prev} = args;
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


async def parse_items(query: str, max_pages: int, region: str, salary_from: str):
    results = []
    logger.info("Starting parser...")
    logger.info(f"Searching query: {query}")

    async with async_playwright() as p:
        logger.info("Browser starting...")
        browser = await p.chromium.launch(headless=config['HEADLESS'], slow_mo=50)
        page = await browser.new_page()

        logger.info("Following link...")
        await page.goto(config['BASE_URL_HHRU'], timeout=60_000)

        logger.info("Entering a query...")
        await page.fill(selectors.SEARCH_INPUT, query)
        await page.keyboard.press("Enter")
        
        await select_region(page, region)
        await specify_salary_from(page, salary_from)

        for page_number in range(max_pages):
            
            logger.info(f"Page number {page_number + 1}")

            try:
                await page.wait_for_selector(selectors.VACANCY_CARD)
            except Exception:
                logger.exception("No vacancies loaded")
                return results
            
            await auto_scroll(page, config['SCROLL_TIMES'], config['SCROLL_PAUSE'])
            
            cards = page.locator(selectors.VACANCY_CARD)
            count = await cards.count()
            logger.info(f"Vacancies found: {count}")
            
            tasks = [
                parse_card_limited(cards.nth(i))
                for i in range(count)
            ]
            page_results = await asyncio.gather(*tasks)
            results.extend(page_results)
            
            # Try to click the standard "next page" button first
            next_page_button = page.locator(selectors.NEXT_PAGE_BUTTON)
            if await next_page_button.count() > 0:
                await next_page_button.click()
                continue
            
            # If the explicit next button is missing, fall back to pagination numbers
            page_buttons = page.locator(selectors.PAGER_PAGE)
            if await page_buttons.count() == 0:
                logger.info("NO pagination controls found – ending pagination")
                break
            
            # Determine the currently active page (has aria-current="true")
            current_button = page.locator(f"{selectors.PAGER_PAGE}[aria-current='true']")
            if await current_button.count() == 0:
                # If no button is marked as current, assume we are on the first page
                current_index = 0
            else:
                # Extract the page number text and convert to zero‑based index
                current_text = await current_button.first.text_content()
                try:
                    current_index = int(current_text.strip()) - 1
                except Exception:
                    current_index = 0
            
            # Click the next page number if it exists
            next_index = current_index + 1
            if next_index < await page_buttons.count():
                await page_buttons.nth(next_index).click()
                continue
            else:
                logger.info("Reached last pagination button – ending pagination")
                break
        
        logger.info("Closing browser...")
        await browser.close()
    
    logger.info("Ending parser...")
    return results


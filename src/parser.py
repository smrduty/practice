from playwright.async_api import async_playwright

from config import BASE_URL, HEADLESS, SCROLL_TIMES, SCROLL_PAUSE, MAX_PAGES
from logger import logger
from utils import auto_scroll

async def parse_items(query: str):
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
        await page.fill("input[data-qa='search-input']", query)
        await page.keyboard.press("Enter")

        await page.keyboard.press("Escape")

        #logger.info("Waiting for vacancies...")
        for page_number in range(MAX_PAGES):
            
            logger.info(f"Page number {page_number + 1}")

            try:
                await page.wait_for_selector("[data-qa='vacancy-serp__vacancy']")
            except Exception:
                logger.exception("No vacancies loaded")
                return results
            
            await auto_scroll(page, SCROLL_TIMES, SCROLL_PAUSE)
            
            cards = page.locator("[data-qa='vacancy-serp__vacancy']")
            count = await cards.count()
            logger.info(f"Vacancies found: {count}")
            for i in range(count):
                card = cards.nth(i)
                try:
                    title = await card.locator("[data-qa='serp-item__title-text']").text_content()
                except Exception as e:
                    logger.warning(f"Couldn't get vacancy title{e}")
                    title = None
                
                try:
                    salary_locator = card.locator("div[class^='compensation-labels'] > span")
                    salary = await salary_locator.first.inner_text() if await salary_locator.count() else None
                except Exception as e:
                    logger.warning(f"Couldn't get vacancy salary{e}")
                    salary = None

                try:
                    experience_locator = card.locator("[data-qa^='vacancy-serp__vacancy-work-experience-']:visible")
                    experience = (await experience_locator.first.text_content()).strip() if await experience_locator.count() else ""
                except Exception as e:
                    logger.warning(f"Couldn't get an experience{e}")
                    experience = None
                
                try:
                    address_locator = card.locator("[data-qa='vacancy-serp__vacancy-address']:visible")
                    address = (await address_locator.text_content()).strip() if await address_locator.count() else ""
                    additional_address_locator = card.locator("[data-qa='address-metro-station-name']:visible")
                    additional_address = (await additional_address_locator.text_content()).strip() if await additional_address_locator.count() else ""
                    complete_address = address + " " + additional_address
                except Exception as e:
                    logger.warning(f"Got a problem with an address...{e}")
                    complete_address = ""

                try:
                    url_locator = card.locator("[data-qa='serp-item__title']")
                    url = await url_locator.get_attribute("href") if await url_locator.count() else None
                except Exception as e:
                    logger.warning(f"Couldn't get vacancy URL")
                    url = None

                #data-qa="vacancy-serp__vacancy-address"
                #data-qa="address-metro-station-name"

                results.append({
                    "title": title,
                    "salary": salary,
                    "experience": experience,
                    "address": complete_address,
                    "url": url
                })

            next_page_button = page.locator("[data-qa='pager-next']")
            if await next_page_button.count() == 0:
                logger.info("NO next page button")
                break

            await next_page_button.click()
            #await page.wait_for_load_state("networkidle", timeout=30000)

        logger.info("Closing browser...")
        await browser.close()

    logger.info("Ending parser...")
    return results


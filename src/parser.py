from playwright.async_api import async_playwright

async def parse_items(query: str):
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()
        await page.goto("https://hh.ru/")
        await page.fill("input[data-qa='search-input']", query)
        await page.keyboard.press("Enter")

        #await page.locator("header [type='button']").click()
        await page.keyboard.press("Escape")
        #await page.locator('xpath="/html/body/div[17]/div/div[1]/div[1]/div/div[2]/button"').click()


        await page.wait_for_selector("[data-qa='vacancy-serp__vacancy']")
        cards = page.locator("[data-qa='vacancy-serp__vacancy']")
        count = await cards.count()
        for i in range(count):
            card = cards.nth(i)
            title = await card.locator("[data-qa='serp-item__title-text']").text_content()
            
            salary_locator = card.locator("div[class^='compensation-labels'] > span")
            if await salary_locator.count() > 0:
                salary = await salary_locator.first.inner_text()
            else:
                salary = None

            results.append({
                "title": title,
                "salary": salary
            })


        await browser.close()

    return results


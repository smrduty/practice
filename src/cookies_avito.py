from playwright.async_api import async_playwright
import asyncio

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # ОБЯЗАТЕЛЬНО
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            locale="ru-RU",
        )

        page = await context.new_page()
        await page.goto("https://www.avito.ru", wait_until="commit")

        print("👉 Пройди проверку вручную, потом нажми Enter в консоли")
        input()

        await context.storage_state(path="avito_state.json")
        print("✅ Cookies сохранены")

        await browser.close()

asyncio.run(main())



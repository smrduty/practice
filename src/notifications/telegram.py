import httpx
from config import config
from db import get_random_no_experience_vacancy
from filters import format_random_vacancy_message
import asyncio
from db import init_db


async def send_telegram_message(text: str):
    # if not config["TELEGRAM_ENABLED"]:
    #     return

    url = (
        f"https://api.telegram.org/bot"
        f"{config['TELEGRAM_BOT_TOKEN']}/sendMessage"
    )

    payload = {
        "chat_id": config["TELEGRAM_CHAT_ID"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json=payload)

async def send_random_no_experience_vacancy(conn):
    vacancy = get_random_no_experience_vacancy(conn)
    if not vacancy:
        print("NO VACANCIES WITHOUT EXPERIENCE")
        return

    print("Sending vacancy:", vacancy.title)
    message = format_random_vacancy_message(vacancy)
    await send_telegram_message(message)

async def main():
    conn = init_db()
    try:
        await send_random_no_experience_vacancy(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())


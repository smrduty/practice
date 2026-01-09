import pandas as pd
import asyncio
import argparse
from datetime import datetime
from parser import parse_items
from config import SEARCH_QUERY
from config import RESULTS_PATH
from config import MAX_PAGES
from dataclasses import asdict
from typing import List
from models import Vacancy
from db import init_db, save_vacancy

parser = argparse.ArgumentParser(
    description="Job parser hh.ru"
)

parser.add_argument(
    "--query",
    type=str,
    default=SEARCH_QUERY,
    help="Search query(by default from .env)"
)

parser.add_argument(
    "--pages",
    type=int,
    default=MAX_PAGES,
    help="Max pages to parse(by default from .env)"
)

args = parser.parse_args()

async def main() -> None:
    vacancies: List[Vacancy] = await parse_items(args.query, args.pages)

    conn = init_db()

    for vacancy in vacancies:
        save_vacancy(conn, vacancy)

    conn.close()
    # rows = [asdict(vacancy) for vacancy in vacancies]
    # df = pd.DataFrame(rows)
    # df.drop_duplicates(subset=["url"], inplace=True)
    # df["parsed_at"] = datetime.now().isoformat()
    # df["query"] = args.query
    # df.to_csv(RESULTS_PATH, index=False, encoding='utf-8')
    


if __name__ == "__main__":
    asyncio.run(main())




import pandas as pd
import asyncio
import argparse
from datetime import datetime
from parser import parse_items
from config import config
from dataclasses import asdict
from typing import List
from models import Vacancy
from db import init_db, save_vacancy
from notifications.telegram import send_random_no_experience_vacancy
from parsers_registry import PARSERS
from logger import logger

parser = argparse.ArgumentParser(
    description="Job parser hh.ru"
)

parser.add_argument(
    "--query",
    type=str,
    default=config['SEARCH_QUERY'],
    help="Search query(by default from .env)"
)

parser.add_argument(
    "--pages",
    type=int,
    default=config['MAX_PAGES'],
    help="Max pages to parse(by default from .env)"
)

parser.add_argument(
    "--region",
    type=str,
    default=config['REGION'],
    help="Region to parse(by default from .env)"
)

# Salary filter argument (minimum salary)
parser.add_argument(
    "--salary-from",
    type=str,
    default=config['SALARY_FROM'],
    help="Minimum salary to filter vacancies (by default from .env)"
)

parser.add_argument(
    "--sites",
    nargs="+",
    default=["hh"],
    help="Sites to parse (hh,  avito, ...)"
)


#args = parser.parse_args()

async def collect_vacancies(args) -> List[Vacancy]:
    all_vacancies: List[Vacancy] = []

    for site in args.sites:
        parser_cls = PARSERS[site]

        if not parser_cls:
            logger.warning(f"Parser for site: '{site}' not found, skipping...")
            continue
        
        logger.info(f"Running parser for site: '{site}'")
        parser = parser_cls()
        site_vacancies = await parser.parse(
            query=args.query,
            max_pages=args.pages,
            region=args.region,
            salary_from=args.salary_from
        )

        all_vacancies.extend(site_vacancies)
    
    return all_vacancies

async def main() -> None:
    args = parser.parse_args()
    vacancies = await collect_vacancies(args)

    if not vacancies:
        logger.warning("No vacancies found...")
        return

    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vacancies;")
    conn.commit()

    for vacancy in vacancies:
        save_vacancy(conn, vacancy)

    rows = [asdict(vacancy) for vacancy in vacancies]
    df = pd.DataFrame(rows)
    df.drop_duplicates(subset=["url"], inplace=True)
    df["parsed_at"] = datetime.now().isoformat()
    df["query"] = args.query
    df.to_csv(config['RESULTS_PATH'], index=False, encoding='utf-8')

    await send_random_no_experience_vacancy(conn)

    conn.close()
    


if __name__ == "__main__":
    asyncio.run(main())




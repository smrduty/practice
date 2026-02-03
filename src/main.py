import pandas as pd
import asyncio
import argparse
from datetime import datetime
from parser import parse_items
from config import config
from dataclasses import asdict, dataclass
from typing import List
from models import Vacancy, ParserConfig
from db import init_db, save_vacancy
from notifications.telegram import send_random_no_experience_vacancy
from parsers_registry import PARSERS
from logger import logger
from utils.last_config import save_last_config, load_last_config
import sys

import tkinter as tk
from tkinter import ttk, messagebox

# def run_parser():
#     config = {
#         "region": region_var.get(),
#         "pages": int(pages_var.get()),
#         "salary": int(salary_var.get()),
#         "sites": [s for s in PARSERS.keys()]
#     }

#     print("Конфигурация:", config)
#     root.destroy()  # закрыть окно

def run_gui() -> ParserConfig:
    root = tk.Tk()
    root.title("Парсер вакансий")
    root.geometry("300x360")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    # ---- Переменные ----
    query_var = tk.StringVar(value="")
    region_var = tk.StringVar(value="")
    pages_var = tk.StringVar(value="")
    salary_var = tk.StringVar(value="")

    site_vars = {
        name: tk.BooleanVar(value=False)
        for name in PARSERS.keys()
    }

    result = {}

    def load_last_cfg():
        last_config = load_last_config()
        if not last_config:
            messagebox.showinfo("Information", "Last config not found")
            logger.warning("NO last config")    
            return
        
        query_var.set(last_config.query)
        region_var.set(last_config.region)
        pages_var.set(last_config.pages)
        salary_var.set(last_config.salary_from)

        for name, var in site_vars.items():
            var.set(name in last_config.sites)


    def safe_int(value, default):
        return int(value) if value.isdigit() else default
    
    def submit():
        result["config"] = ParserConfig(
            query=query_var.get(),
            region=region_var.get(),
            pages=safe_int(pages_var.get(), config["MAX_PAGES"]),
            salary_from=safe_int(salary_var.get(), config["SALARY_FROM"]),
            sites=[k for k, v in site_vars.items() if v.get()]
        )
        root.destroy()

    # ---- UI ----
    ttk.Label(root, text="Вакансия").pack(anchor="w", padx=10, pady=(10, 0))
    ttk.Entry(root, textvariable=query_var).pack(fill="x", padx=10)

    ttk.Label(root, text="Регион").pack(anchor="w", padx=10, pady=(10, 0))
    ttk.Entry(root, textvariable=region_var).pack(fill="x", padx=10)

    ttk.Label(root, text="Страниц").pack(anchor="w", padx=10, pady=(10, 0))
    ttk.Entry(root, textvariable=pages_var).pack(fill="x", padx=10)

    ttk.Label(root, text="Мин. зарплата").pack(anchor="w", padx=10, pady=(10, 0))
    ttk.Entry(root, textvariable=salary_var).pack(fill="x", padx=10)

    ttk.Label(root, text="Сайты").pack(anchor="w", padx=10, pady=(10, 0))
    for name, var in site_vars.items():
        ttk.Checkbutton(root, text=name, variable=var).pack(anchor="w", padx=20)

    ttk.Button(root, text="🕘 Последний запрос", command=load_last_cfg).pack(pady=(10, 0))

    ttk.Button(root, text="▶ Запустить", command=submit).pack(padx=15,pady=(15,0))

    root.mainloop()
    return result["config"]

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Job parser")

    parser.add_argument("--query", default=config['SEARCH_QUERY'], help="Search query(by default from .env)")
    parser.add_argument("--pages", type=int, default=config['MAX_PAGES'], help="Max pages to parse(by default from .env)")
    parser.add_argument("--region", default=config['REGION'], help="Region to parse(by default from .env)")
    parser.add_argument("--salary-from", type=int, default=config['SALARY_FROM'], help="Minimum salary to filter vacancies (by default from .env)")
    parser.add_argument("--use-last-config", action="store_true", help="Use last saved parser config")
    parser.add_argument(
        "--sites",
        nargs="+",
        choices=PARSERS.keys(),
        default=["hh"],
        help="Sites to parse (hh,  avito, ...)"
    )

    return parser

def get_config() -> ParserConfig:
    parser = build_arg_parser()

    if len(sys.argv) == 1:
        logger.info("No CLI args, opening GUI")
        return run_gui()

    args = parser.parse_args()

    if args.use_last_config:
        last_cfg = load_last_config()
        if not last_cfg:
            raise RuntimeError("Last config not found")
        return last_cfg


    return ParserConfig(
            query=args.query,
            region=args.region,
            pages=args.pages,
            salary_from=args.salary_from,
            sites=args.sites
        )

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
    cfg = get_config()
    save_last_config(cfg)
    vacancies = await collect_vacancies(cfg)

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
    df["query"] = cfg.query
    df.to_csv(config['RESULTS_PATH'], index=False, encoding='utf-8')

    await send_random_no_experience_vacancy(conn)

    conn.close()
    


if __name__ == "__main__":
    asyncio.run(main())




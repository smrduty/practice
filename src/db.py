import sqlite3
from datetime import datetime
from models import Vacancy

def init_db(path: str = "vacancies.db"):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vacancies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        salary TEXT,
        salary_from INTEGER,
        salary_to INTEGER,
        experience TEXT,
        address TEXT,
        url TEXT UNIQUE,
        parsed_at TEXT   
    )
    """)

    conn.commit()
    return conn

def save_vacancy(conn, vacancy: Vacancy):
    cursor = conn.cursor()

    salary_from, salary_to = vacancy.parse_salary()

    cursor.execute("""
    INSERT OR IGNORE INTO vacancies
    (title, salary, salary_from, salary_to, experience, address, url, parsed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vacancy.title,
        vacancy.salary,
        salary_from,
        salary_to,
        vacancy.experience,
        vacancy.address,
        vacancy.url,
        datetime.now().isoformat()
    ))

    conn.commit()



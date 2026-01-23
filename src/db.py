import sqlite3
from datetime import datetime
from models import Vacancy
import random
from config import config

def init_db():
    db_path = config["DB_PATH"]
    conn = sqlite3.connect(db_path)
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

def get_random_no_experience_vacancy(conn):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT title, salary, experience, address, url
        FROM vacancies
        WHERE experience IS NOT NULL
          AND (
            experience LIKE '%без опыта%' COLLATE NOCASE
            OR experience LIKE '%Без опыта%' COLLATE NOCASE
            )
        """
    )

    rows = cursor.fetchall()
    if not rows:
        return None

    row = random.choice(rows)

    return Vacancy(
        title=row[0],
        salary=row[1],
        experience=row[2],
        address=row[3],
        url=row[4],
    )



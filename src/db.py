import sqlite3
from datetime import datetime
from models import Vacancy
from typing import List, Optional, Dict

def init_db(path: str = "vacancies.db"):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
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
    """
    )

    conn.commit()
    return conn

def save_vacancy(conn, vacancy: Vacancy):
    cursor = conn.cursor()

    salary_from, salary_to = vacancy.parse_salary()

    url = vacancy.full_url() or vacancy.url

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
        url,
        datetime.now().isoformat()
    ))

    conn.commit()

def _row_to_dict(row: sqlite3.Row) -> Dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "salary": row["salary"],
        "salary_from": row["salary_from"],
        "salary_to": row["salary_to"],
        "experience": row["experience"],
        "address": row["address"],
        "url": row["url"],
        "parsed_at": row["parsed_at"]
    }

def fetch_vacancies(conn, limit: int = 100, search: Optional[str] = None, by_id: Optional[int] = None) -> List[Dict]:
    cursor = conn.cursor()

    if by_id is not None:
        cursor.execute("SELECT * FROM vacancies WHERE id = ? LIMIT 1", (by_id,))
        row = cursor.fetchone()
        return [_row_to_dict(row)] if row else []

    if search:
        q = f"%{search}%"
        cursor.execute("""
            SELECT * FROM vacancies
            WHERE title LIKE ? OR address LIKE ? OR experience LIKE ? OR url LIKE ?
            ORDER BY parsed_at DESC
            LIMIT ?
        """, (q, q, q, q, limit))
    else:
        cursor.execute("""
            SELECT * FROM vacancies
            ORDER BY parsed_at DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    return [_row_to_dict(r) for r in rows]
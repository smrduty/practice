from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional
import sqlite3
import db

from notifications.telegram import send_telegram_message

app = FastAPI(title="Vacancy API")

# Mount static files
static_dir = Path(__file__).parent / "web" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "web" / "templates"))

# Allow simple CORS for the UI if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/vacancies")
def api_vacancies(limit: Optional[int] = 1000, q: Optional[str] = None):
    conn = db.init_db()
    try:
        rows = db.fetch_vacancies(conn, limit=limit, search=q)
        return JSONResponse(content={"count": len(rows), "items": rows})
    finally:
        conn.close()

@app.get("/api/vacancies/{vacancy_id}")
def api_vacancy(vacancy_id: int):
    conn = db.init_db()
    try:
        rows = db.fetch_vacancies(conn, limit=1, by_id=vacancy_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        return JSONResponse(content=rows[0])
    finally:
        conn.close()

@app.get("/api/stats/count")
def vacancies_count():
    conn = db.init_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vacancies")
    total = cursor.fetchone()[0]

    conn.close()
    return {"total": total}

@app.delete("/api/vacancies/{vacancy_id}")
def delete_vacancy(vacancy_id: int):
    conn = db.init_db()
    try:
        ok = db.delete_vacancy_by_id(conn, vacancy_id)
        
        if not ok:
            raise HTTPException(status_code=404, detail="Vacancy not found")

        return {"status": "ok", "deleted_id": vacancy_id}
    finally:
        conn.close()

@app.post("/api/vacancies/{vacancy_id}/send_to_tg")
async def send_vacancy_to_tg(vacancy_id: int):
    conn = db.init_db()
    try:
        rows = db.fetch_vacancies(conn, limit=1, by_id=vacancy_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        
        v = rows[0]

        text = (
            f"<b>{v.get('title','')}</b>\n"
            f"🏢 {v.get('experience','')}\n"
            f"💰 {v.get('salary','')}\n"
            f"📍 {v.get('address','')}\n\n"
            f"<a href='{v.get('url','')}'>Открыть вакансию</a>"
        )

        await send_telegram_message(text)

        return {'status': 'ok'}
    
    finally:
        conn.close()
        




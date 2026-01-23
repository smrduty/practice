from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional
import sqlite3
from db import init_db, fetch_vacancies

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
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/vacancies")
def api_vacancies(limit: Optional[int] = 100, q: Optional[str] = None):
    conn = init_db()
    try:
        rows = fetch_vacancies(conn, limit=limit, search=q)
        return JSONResponse(content={"count": len(rows), "items": rows})
    finally:
        conn.close()

@app.get("/api/vacancies/{vacancy_id}")
def api_vacancy(vacancy_id: int):
    conn = init_db()
    try:
        rows = fetch_vacancies(conn, limit=1, by_id=vacancy_id)
        if not rows:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        return JSONResponse(content=rows[0])
    finally:
        conn.close()
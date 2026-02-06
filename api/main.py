from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
import sqlite3

app = FastAPI(title="Face Attendance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "attendance.db"

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

@app.on_event("startup")
def startup():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.post("/attendance")
def mark_attendance(name: str):
    now = datetime.now()
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO attendance (name, date, time) VALUES (?, ?, ?)",
        (name, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "name": name}

@app.get("/attendance/today")
def today_attendance():
    today = date.today().strftime("%Y-%m-%d")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM attendance WHERE date=?", (today,))
    present = [r[0] for r in cur.fetchall()]
    conn.close()
    return {"date": today, "present": present, "count": len(present)}

@app.get("/")
def root():
    return {"status": "API running"}

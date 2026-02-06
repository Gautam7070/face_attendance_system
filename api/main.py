from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
from pydantic import BaseModel
import sqlite3

class AttendanceItem(BaseModel):
    name: str
    timestamp: str = None
    type: str = "Punch-In"

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
            time TEXT,
            type TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.post("/attendance")
def mark_attendance(item: AttendanceItem):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO attendance (name, date, time, type) VALUES (?, ?, ?, ?)",
        (item.name, date_str, time_str, item.type)
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "name": item.name, "type": item.type}

@app.get("/attendance/today")
def today_attendance():
    today = date.today().strftime("%Y-%m-%d")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name, time, type FROM attendance WHERE date=?", (today,))
    records = [{"name": r[0], "time": r[1], "type": r[2]} for r in cur.fetchall()]
    conn.close()
    return {"date": today, "records": records, "count": len(records)}

@app.get("/")
def root():
    return {"status": "API running"}

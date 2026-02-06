from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import date
from database import engine, SessionLocal
from models import Attendance, Base
from schemas import AttendanceCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Face Attendance API")

# ================= DB =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= POST =================
@app.post("/attendance")
def mark_attendance(data: AttendanceCreate, db: Session = Depends(get_db)):
    record = Attendance(
        name=data.name,
        type=data.type
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"status": "success"}

# ================= GET =================
@app.get("/attendance/today")
def today_attendance(db: Session = Depends(get_db)):
    today = date.today()
    records = db.query(Attendance).all()

    return [
        {
            "name": r.name,
            "type": r.type,
            "timestamp": r.timestamp
        }
        for r in records
        if r.timestamp.date() == today
    ]

@app.get("/attendance/present")
def present_users(db: Session = Depends(get_db)):
    today = date.today()
    records = db.query(Attendance).all()

    latest = {}
    for r in records:
        if r.timestamp.date() == today:
            latest[r.name] = r.type

    return [name for name, t in latest.items() if t == "Punch-In"]

@app.get("/attendance/stats")
def stats(db: Session = Depends(get_db)):
    users = db.query(Attendance.name).distinct().count()
    present = len(present_users(db))
    percent = (present / users * 100) if users else 0

    return {
        "total_users": users,
        "present": present,
        "attendance_percent": round(percent, 2)
    }

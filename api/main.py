import sys
import os
from datetime import datetime

# Add parent directory to path to allow importing from 'security' and 'api'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import cv2
import face_recognition

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from security.liveness import LivenessDetector
from alerts.whatsapp import send_whatsapp_alert
from api.database import (
    load_encodings,
    save_encodings,
    read_attendance,
    mark_attendance
)

# ================= APP INIT =================

app = FastAPI(title="Face Attendance Admin API")

# ================= CORS CONFIG =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # allow all origins (frontend, admin panel, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent Liveness Detector for API Replay/Motion Check
api_liveness = LivenessDetector()

# ================= BASIC =================

@app.get("/")
def root():
    return {"status": "Face Attendance API running"}

# ================= ATTENDANCE =================

@app.get("/attendance/today")
def today_attendance():
    df = read_attendance()
    today = datetime.now().strftime("%Y-%m-%d")
    today_df = df[df["Date"] == today]
    return today_df.to_dict(orient="records")

@app.get("/attendance/present")
def present_list():
    df = read_attendance()
    today = datetime.now().strftime("%Y-%m-%d")
    present = df[df["Date"] == today]["Name"].unique().tolist()
    return {"present": present}

@app.get("/attendance/absent")
def absent_list():
    data = load_encodings()
    all_users = set(data["names"])

    df = read_attendance()
    today = datetime.now().strftime("%Y-%m-%d")
    present = set(df[df["Date"] == today]["Name"].unique())

    absent = list(all_users - present)
    return {"absent": absent}

@app.get("/attendance/percentage")
def attendance_percentage():
    data = load_encodings()
    total = len(set(data["names"]))

    if total == 0:
        return {"attendance_percentage": 0}

    df = read_attendance()
    today = datetime.now().strftime("%Y-%m-%d")
    present = df[df["Date"] == today]["Name"].nunique()

    percentage = round((present / total) * 100, 2)
    return {"attendance_percentage": percentage}

# ================= FACE REGISTRATION =================

@app.post("/register-face")
async def register_face(file: UploadFile = File(...), name: str = ""):
    if not name:
        return {"error": "Name is required"}

    image_bytes = await file.read()
    np_img = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Resize for faster processing
    small_rgb = cv2.resize(rgb, (0, 0), fx=0.25, fy=0.25)

    locations = face_recognition.face_locations(small_rgb)
    encodings = face_recognition.face_encodings(small_rgb, locations)

    if not encodings:
        return {"error": "No face detected"}

    data = load_encodings()
    data["encodings"].append(encodings[0])
    data["names"].append(name)

    save_encodings(data)

    return {"message": f"Face registered for {name}"}

# ================= MARK ATTENDANCE =================

@app.post("/mark-attendance")
async def api_mark_attendance(file: UploadFile = File(...)):
    image_bytes = await file.read()
    np_img = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Resize for faster processing
    small_rgb = cv2.resize(rgb, (0, 0), fx=0.25, fy=0.25)

    locations = face_recognition.face_locations(small_rgb)
    encodings = face_recognition.face_encodings(small_rgb, locations)

    # ---------- SECURITY: LIVENESS CHECKS ----------
    if not api_liveness.detect_motion(image):
        return {"error": "Spoof detected: no motion / static photo"}

    if not api_liveness.detect_replay(image):
        return {"error": "Replay attack detected: reused image"}
    # ----------------------------------------------

    if not encodings:
        return {"error": "No face detected"}

    data = load_encodings()
    known_encs = data.get("encodings", [])
    known_names = data.get("names", [])

    if not known_encs:
        return {"error": "No faces registered in the system"}

    distances = face_recognition.face_distance(known_encs, encodings[0])
    min_dist = np.min(distances)

    if min_dist > 0.5:
        return {"error": "Face not recognized"}

    idx = np.argmin(distances)
    name = known_names[idx]

    record_type = mark_attendance(name)
    send_whatsapp_alert(name, record_type)

    return {
        "name": name,
        "type": record_type,
        "status": "Attendance marked"
    }

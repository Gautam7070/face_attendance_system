import cv2
import face_recognition
import pickle
import numpy as np
import pandas as pd
import os
from datetime import datetime
from scipy.spatial import distance as dist

# ===================== SAFE OPTIONAL IMPORTS =====================
try:
    from spoof_detection import is_blink
except ImportError:
    is_blink = None  # fallback

try:
    from utils import send_to_cloud
except ImportError:
    def send_to_cloud(payload):
        return False  # safe fallback
# ================================================================

# ===================== CONFIG =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ENCODINGS_FILE = os.path.join(BASE_DIR, "data", "encodings.pkl")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance", "attendance.csv")

FACE_THRESHOLD = 0.5
EYE_AR_THRESHOLD = 0.25
EYE_AR_CONSEC_FRAMES = 3
# =================================================

os.makedirs(os.path.dirname(ATTENDANCE_FILE), exist_ok=True)

# ===================== LOAD ENCODINGS =====================
known_encodings = []
known_names = []

if os.path.exists(ENCODINGS_FILE) and os.path.getsize(ENCODINGS_FILE) > 0:
    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)

    # Supports BOTH old and new encoding formats
    if isinstance(data, dict):
        if "encodings" in data and "names" in data:
            for enc, name in zip(data["encodings"], data["names"]):
                known_encodings.append(enc)
                known_names.append(name)
        else:
            for name, encs in data.items():
                for enc in encs:
                    known_encodings.append(enc)
                    known_names.append(name)

print(f"[INFO] Loaded {len(known_encodings)} face encodings")

# ===================== ATTENDANCE FILE =====================
if not os.path.exists(ATTENDANCE_FILE) or os.path.getsize(ATTENDANCE_FILE) == 0:
    df = pd.DataFrame(columns=["Name", "Date", "Time", "Type"])
    df.to_csv(ATTENDANCE_FILE, index=False)

# ===================== BLINK HELPERS =====================
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# ===================== ATTENDANCE =====================
def mark_attendance(name):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    df = pd.read_csv(ATTENDANCE_FILE)

    today_records = df[(df["Name"] == name) & (df["Date"] == date)]

    record_type = "Punch-In" if len(today_records) == 0 else (
        "Punch-Out" if today_records.iloc[-1]["Type"] == "Punch-In" else "Punch-In"
    )

    df.loc[len(df)] = [name, date, time, record_type]
    df.to_csv(ATTENDANCE_FILE, index=False)

    payload = {
        "name": name,
        "timestamp": f"{date} {time}",
        "type": record_type
    }

    cloud_status = send_to_cloud(payload)
    print(f"[ATTENDANCE] {name} | {record_type} | {'Cloud' if cloud_status else 'Local'}")

    return record_type

# ===================== CAMERA SAFE INIT =====================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("[ERROR] Camera not accessible (cloud environment?)")
    exit(0)

blink_counter = 0
blink_detected = False
process_this_frame = True

# ===================== MAIN LOOP =====================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        scaled_locations = [(t*4, r*4, b*4, l*4) for t, r, b, l in face_locations]
        face_landmarks = face_recognition.face_landmarks(frame, scaled_locations)

    process_this_frame = not process_this_frame

    for i, (encoding, loc) in enumerate(zip(face_encodings, face_locations)):
        name = "Unknown"
        confidence = 0
        color = (0, 0, 255)

        if known_encodings:
            distances = face_recognition.face_distance(known_encodings, encoding)
            best_match = np.argmin(distances)
            if distances[best_match] < FACE_THRESHOLD:
                name = known_names[best_match]
                confidence = round((1 - distances[best_match]) * 100, 2)
                color = (0, 255, 0)

        # ---------- BLINK ----------
        if i < len(face_landmarks):
            lm = face_landmarks[i]
            if "left_eye" in lm and "right_eye" in lm:
                ear = (
                    eye_aspect_ratio(lm["left_eye"]) +
                    eye_aspect_ratio(lm["right_eye"])
                ) / 2

                if ear < EYE_AR_THRESHOLD:
                    blink_counter += 1
                else:
                    if blink_counter >= EYE_AR_CONSEC_FRAMES:
                        blink_detected = True
                    blink_counter = 0

        # ---------- ATTENDANCE ----------
        if blink_detected and name != "Unknown":
            record = mark_attendance(name)
            cv2.putText(frame, f"{name} {record}", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Face Attendance System", frame)
            
            cv2.waitKey(2000) # Show success for 2 seconds
            cap.release()
            cv2.destroyAllWindows()
            print(f"[SUCCESS] {name} logged as {record}")
            os._exit(0) # Exit entirely

        top, right, bottom, left = [v * 4 for v in loc]
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, f"{name} ({confidence}%)",
                    (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Face Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

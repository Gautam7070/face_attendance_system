import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime
from scipy.spatial import distance as dist
import pandas as pd
import os
import winsound

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODINGS_FILE = os.path.join(BASE_DIR, "data", "encodings.pkl")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance", "attendance.csv")

FACE_THRESHOLD = 0.5
EYE_AR_THRESHOLD = 0.25
EYE_AR_CONSEC_FRAMES = 3
# =========================================

# Load encodings safely
data = {}
if os.path.exists(ENCODINGS_FILE) and os.path.getsize(ENCODINGS_FILE) > 0:
    with open(ENCODINGS_FILE, "rb") as f:
        try:
            data = pickle.load(f)
        except (EOFError, pickle.UnpicklingError):
            data = {}

known_encodings = []
known_names = []

if isinstance(data, dict):
    # Case 1: New parallel list structure {"encodings": [...], "names": [...]}
    if "encodings" in data and "names" in data:
        for enc, name in zip(data["encodings"], data["names"]):
            if hasattr(enc, "shape") and enc.shape == (128,):
                known_encodings.append(enc)
                known_names.append(name)
    # Case 2: Old structure {name: [enc1, enc2, ...]}
    else:
        for name, encs in data.items():
            if isinstance(encs, list):
                for enc in encs:
                    if hasattr(enc, "shape") and enc.shape == (128,):
                        known_encodings.append(enc)
                        known_names.append(name)

# Create attendance file if not exists or is empty
os.makedirs(os.path.dirname(ATTENDANCE_FILE), exist_ok=True)
if not os.path.exists(ATTENDANCE_FILE) or os.path.getsize(ATTENDANCE_FILE) == 0:
    df = pd.DataFrame(columns=["Name", "Date", "Time", "Type"])
    df.to_csv(ATTENDANCE_FILE, index=False)

# ================= FUNCTIONS =================

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def mark_attendance(name):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    try:
        df = pd.read_csv(ATTENDANCE_FILE)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=["Name", "Date", "Time", "Type"])

    # Determine Punch-In / Punch-Out
    records_today = df[(df["Name"] == name) & (df["Date"] == date)]

    if len(records_today) == 0:
        record_type = "Punch-In"
    else:
        last_type = records_today.iloc[-1]["Type"]
        record_type = "Punch-Out" if last_type == "Punch-In" else "Punch-In"

    df.loc[len(df)] = [name, date, time, record_type]
    df.to_csv(ATTENDANCE_FILE, index=False)

    winsound.Beep(1000, 300)
    return record_type

# ============================================

cap = cv2.VideoCapture(0)
process_this_frame = True
blink_counter = 0
blink_detected = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Resize frame to 1/4 size for faster face detection
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # 2. Only process every other frame to save CPU
    if process_this_frame:
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        # Landmarking is still done on full frame for precision if needed, 
        # but passing locations speeds it up significantly
        # Scale locations back up for landmarks
        upscaled_locations = [(t*4, r*4, b*4, l*4) for t, r, b, l in face_locations]
        face_landmarks = face_recognition.face_landmarks(frame, upscaled_locations)

    process_this_frame = not process_this_frame

    for i, (encoding, location) in enumerate(zip(face_encodings, face_locations)):
        name = "Unknown"
        confidence = 0
        color = (0, 0, 255)

        if len(known_encodings) > 0:
            distances = face_recognition.face_distance(known_encodings, encoding)
            if len(distances) > 0:
                min_distance = np.min(distances)
                best_match = np.argmin(distances)

                if min_distance < FACE_THRESHOLD:
                    name = known_names[best_match]
                    confidence = round((1 - min_distance) * 100, 2)
                    color = (0, 255, 0)

        # Get landmarks for this specific face
        if i < len(face_landmarks):
            landmark = face_landmarks[i]
            # ---------- BLINK DETECTION ----------
            if "left_eye" in landmark and "right_eye" in landmark:
                left_eye = landmark["left_eye"]
                right_eye = landmark["right_eye"]
                ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2

                if ear < EYE_AR_THRESHOLD:
                    blink_counter += 1
                else:
                    if blink_counter >= EYE_AR_CONSEC_FRAMES:
                        blink_detected = True
                    blink_counter = 0

        # ---------- ATTENDANCE ----------
        if blink_detected and name != "Unknown":
            record_type = mark_attendance(name)
            cv2.putText(frame, f"{name} - {record_type}", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Face Attendance System", frame)
            cv2.waitKey(2000) 
            cap.release()
            cv2.destroyAllWindows()
            print(f"[INFO] {name} {record_type} success.")
            os._exit(0) 

        # ---------- UI (Scaling back up) ----------
        top, right, bottom, left = [v * 4 for v in location]
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        label = f"{name} ({confidence}%)"
        cv2.putText(frame, label, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Face Attendance System", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

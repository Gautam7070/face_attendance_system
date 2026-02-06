import pandas as pd
import os
from datetime import datetime
import pickle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENCODINGS_FILE = os.path.join(BASE_DIR, "data", "encodings.pkl")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance", "attendance.csv")

# Ensure attendance file exists
if not os.path.exists(ATTENDANCE_FILE):
    df = pd.DataFrame(columns=["Name", "Date", "Time", "Type"])
    df.to_csv(ATTENDANCE_FILE, index=False)

def load_encodings():
    if not os.path.exists(ENCODINGS_FILE) or os.path.getsize(ENCODINGS_FILE) == 0:
        return {"encodings": [], "names": []}

    try:
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)
            if not isinstance(data, dict):
                return {"encodings": [], "names": []}
            
            if "encodings" in data and "names" in data:
                # Filter for valid dimensions
                valid_indices = [i for i, enc in enumerate(data["encodings"]) if hasattr(enc, "shape") and enc.shape == (128,)]
                return {
                    "encodings": [data["encodings"][i] for i in valid_indices],
                    "names": [data["names"][i] for i in valid_indices]
                }
            else:
                # Convert old structure
                new_data = {"encodings": [], "names": []}
                for name, encs in data.items():
                    if isinstance(encs, list):
                        for enc in encs:
                            import numpy as np
                            if hasattr(enc, "shape") and enc.shape == (128,):
                                new_data["encodings"].append(enc)
                                new_data["names"].append(name)
                return new_data
    except:
        return {"encodings": [], "names": []}

def save_encodings(data):
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)

def read_attendance():
    if not os.path.exists(ATTENDANCE_FILE) or os.path.getsize(ATTENDANCE_FILE) == 0:
        return pd.DataFrame(columns=["Name", "Date", "Time", "Type"])
    try:
        return pd.read_csv(ATTENDANCE_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=["Name", "Date", "Time", "Type"])

def write_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)

def mark_attendance(name):
    df = read_attendance()

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    today_records = df[(df["Name"] == name) & (df["Date"] == date)]

    if len(today_records) == 0:
        record_type = "Punch-In"
    else:
        last = today_records.iloc[-1]["Type"]
        record_type = "Punch-Out" if last == "Punch-In" else "Punch-In"

    df.loc[len(df)] = [name, date, time, record_type]
    write_attendance(df)

    return record_type

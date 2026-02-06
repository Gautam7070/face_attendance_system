import sys
import os
# Add parent directory to path to allow importing from 'security'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
from tkinter import messagebox, filedialog
import cv2
import face_recognition
import pickle
import os
import numpy as np
import pandas as pd
import time
from datetime import datetime
import subprocess
import threading
import queue
from PIL import Image, ImageTk
from security.liveness import LivenessDetector
from alerts.whatsapp import send_whatsapp_alert

# ================= CONFIG & PATHS =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENCODINGS_FILE = os.path.join(BASE_DIR, "data", "encodings.pkl")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance", "attendance.csv")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ================= DATA HELPERS =================
def load_data():
    if os.path.exists(ENCODINGS_FILE) and os.path.getsize(ENCODINGS_FILE) > 0:
        with open(ENCODINGS_FILE, "rb") as f:
            try:
                data = pickle.load(f)
                if isinstance(data, dict):
                    # Standardize to new sequence structure
                    if "encodings" in data and "names" in data:
                        # Filter for valid dimensions
                        valid_indices = [i for i, enc in enumerate(data["encodings"]) if hasattr(enc, "shape") and enc.shape == (128,)]
                        return {
                            "encodings": [data["encodings"][i] for i in valid_indices],
                            "names": [data["names"][i] for i in valid_indices]
                        }
                    else:
                        # Old structure {name: [encs]}
                        new_data = {"encodings": [], "names": []}
                        for name, encs in data.items():
                            if isinstance(encs, list):
                                for enc in encs:
                                    if hasattr(enc, "shape") and enc.shape == (128,):
                                        new_data["encodings"].append(enc)
                                        new_data["names"].append(name)
                        return new_data
            except:
                pass
    return {"encodings": [], "names": []}

def save_data(data):
    os.makedirs(os.path.dirname(ENCODINGS_FILE), exist_ok=True)
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(data, f)

# ================= MAIN APP CLASS =================
class FaceAttendanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Biometric Intelligence Portal v2.0")
        self.geometry("1000x650")

        # Grid config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Initialize data
        self.data = load_data()
        self.running_camera = False
        self.cap = None
        
        # Async Processing
        self.frame_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)
        self.current_results = []
        self.recognition_active = False
        
        # Accuracy Tuning: Multi-frame consensus
        self.consensus_count = {} # {name: count}
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="FACIAL INTEL", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_attendance = ctk.CTkButton(self.sidebar_frame, text="Mark Attendance", command=self.show_attendance)
        self.btn_attendance.grid(row=2, column=0, padx=20, pady=10)

        self.btn_register = ctk.CTkButton(self.sidebar_frame, text="Register Identity", command=self.show_registration)
        self.btn_register.grid(row=3, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 20))

        # Main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.show_dashboard()

    def clear_main_frame(self):
        self.stop_camera()
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_frame()
        self.main_frame.grid_rowconfigure(0, weight=0) # Reset row weight
        
        title = ctk.CTkLabel(self.main_frame, text="Enterprise Dashboard", font=ctk.CTkFont(size=28, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 40), sticky="w")

        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, padx=20, sticky="nsew")
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Metrics cards
        self.create_metric_card(stats_frame, "Total Identities", len(set(self.data["names"])), 0)
        
        today = datetime.now().strftime("%Y-%m-%d")
        log_df = pd.read_csv(ATTENDANCE_FILE) if os.path.exists(ATTENDANCE_FILE) else pd.DataFrame()
        today_count = log_df[log_df["Date"] == today]["Name"].nunique() if not log_df.empty else 0
        self.create_metric_card(stats_frame, "Marked Today", today_count, 1)
        
        self.create_metric_card(stats_frame, "System Status", "SECURE", 2)

    def create_metric_card(self, parent, label, value, col):
        card = ctk.CTkFrame(parent, corner_radius=15)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
        
        lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=14))
        lbl.pack(pady=(15, 5))
        
        val = ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=32, weight="bold"), text_color="#00f2fe")
        val.pack(pady=(0, 15))

    def show_attendance(self):
        self.clear_main_frame()
        
        title = ctk.CTkLabel(self.main_frame, text="Real-time Recognition", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=20)

        self.cam_label = ctk.CTkLabel(self.main_frame, text="")
        self.cam_label.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.btn_action = ctk.CTkButton(self.main_frame, text="Start Scanner", command=self.start_camera_recognition)
        self.btn_action.grid(row=2, column=0, padx=20, pady=20)

    def start_camera_recognition(self):
        if not self.running_camera:
            self.cap = cv2.VideoCapture(0)
            self.running_camera = True
            self.liveness = LivenessDetector()
            self.btn_action.configure(text="Stop Scanner", fg_color="red")
            
            # Start Background Worker
            self.recognition_active = True
            threading.Thread(target=self.recognition_worker, daemon=True).start()
            
            self.update_camera_frame()

    def recognition_worker(self):
        """ Background thread for heavy AI processing """
        while self.recognition_active:
            try:
                frame = self.frame_queue.get(timeout=1)
                # 1. Resize for speed
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                # 2. Detect & Encode
                locs = face_recognition.face_locations(rgb_small_frame)
                encs = face_recognition.face_encodings(rgb_small_frame, locs)
                
                # Upscale locations for landmarks on original frame
                upscaled_locations = [(t*4, r*4, b*4, l*4) for t, r, b, l in locs]
                landmarks = face_recognition.face_landmarks(frame, upscaled_locations)

                results = []
                for enc, loc, landmark in zip(encs, locs, landmarks):
                    name = "Unknown"
                    challenge_ok = self.liveness.verify_challenge(landmark, frame.shape[1])
                    
                    if self.data["encodings"]:
                        dists = face_recognition.face_distance(self.data["encodings"], enc)
                        # Increased threshold to 0.45 for better accuracy
                        if np.min(dists) < 0.45:
                            name = self.data["names"][np.argmin(dists)]
                    
                    # Liveness Check (Motion/Replay)
                    motion_ok = self.liveness.detect_motion(frame) and self.liveness.detect_replay(frame)
                    
                    results.append({
                        "name": name, 
                        "loc": [v * 4 for v in loc], 
                        "challenge_ok": challenge_ok,
                        "motion_ok": motion_ok
                    })
                
                # Update shared results
                if not self.result_queue.full():
                    self.result_queue.put(results)
                    
            except queue.Empty:
                continue

    def update_camera_frame(self):
        if self.running_camera:
            ret, frame = self.cap.read()
            if ret:
                # 1. Push frame to worker (if worker is ready)
                if not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())

                # 2. Pull latest results (Non-blocking)
                try:
                    self.current_results = self.result_queue.get_nowait()
                except queue.Empty:
                    pass

                # 3. Draw overlays using last known results
                for res in self.current_results:
                    name = res["name"]
                    top, right, bottom, left = res["loc"]
                    challenge_ok = res["challenge_ok"]
                    motion_ok = res["motion_ok"]
                    
                    color = (255, 0, 0) # Red (Unknown/Fail)
                    
                    if motion_ok:
                        if name != "Unknown":
                            if challenge_ok:
                                color = (0, 255, 0) # Green (Verified)
                                
                                # ACCURACY: Multi-frame consensus before marking
                                self.consensus_count[name] = self.consensus_count.get(name, 0) + 1
                                
                                if self.consensus_count[name] >= 3:
                                    if not hasattr(self, 'last_marked') or (datetime.now() - self.last_marked).seconds > 10:
                                        self.last_marked = datetime.now()
                                        rectype = self.mark_attendance(name)
                                        send_whatsapp_alert(name, rectype)
                                        self.consensus_count[name] = 0
                                        # Rotate challenge for next person/scan
                                        self.liveness.next_challenge()
                            else:
                                color = (255, 165, 0) # Orange (Pending)
                                self.consensus_count[name] = 0
                    
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    status = f"{name} (VERIFYING...)" if name != "Unknown" and not challenge_ok else name
                    cv2.putText(frame, status, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                # Show Challenge Overlay
                cv2.putText(frame, f"CHALLENGE: {self.liveness.challenge.upper()}", 
                            (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                self.cam_label.imgtk = imgtk
                self.cam_label.configure(image=imgtk)
                self.cam_label.after(5, self.update_camera_frame) # Even faster refresh


    def show_registration(self):
        self.clear_main_frame()
        
        title = ctk.CTkLabel(self.main_frame, text="Biometric Registration", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=20)

        self.name_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Enter Identity Name", width=300)
        self.name_entry.grid(row=1, column=0, padx=20, pady=10)

        self.cam_label = ctk.CTkLabel(self.main_frame, text="Webcam Preview will appear here")
        self.cam_label.grid(row=2, column=0, padx=20, pady=10)

        self.reg_btn = ctk.CTkButton(self.main_frame, text="Start Bulk Capture (20 Photos)", command=self.bulk_capture)
        self.reg_btn.grid(row=3, column=0, padx=20, pady=20)

    def bulk_capture(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a name first.")
            return

        cap = cv2.VideoCapture(0)
        count = 0
        captured_encodings = []

        messagebox.showinfo("Registration", "Webcam will open. Press 'C' once to start Burst Mode (Auto-capture 20 photos).")

        while count < 20:
            ret, frame = cap.read()
            if not ret: break
            
            cv2.putText(frame, f"Identity: {name} | Captured: {count}/20", (30, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 254), 2)
            cv2.imshow("Bulk Capture - Press 'C' to Start Burst", frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # Start automatic capture once 'c' is pressed
            if key == ord('c') or count > 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locs = face_recognition.face_locations(rgb)
                encs = face_recognition.face_encodings(rgb, locs)
                
                if len(encs) == 1:
                    captured_encodings.append(encs[0])
                    count += 1
                    # Small delay to ensure frames vary slightly
                    time.sleep(0.1)
                else:
                    cv2.putText(frame, "KEEP STILL - Face Lost!", (30, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                
            if key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if count == 20:
            self.data["encodings"].extend(captured_encodings)
            self.data["names"].extend([name] * 20)
            save_data(self.data)
            messagebox.showinfo("Success", f"Identity '{name}' successfully enrolled.")
            self.show_dashboard()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def stop_camera(self):
        self.running_camera = False
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    def mark_attendance(self, name):
        df = pd.read_csv(ATTENDANCE_FILE) if os.path.exists(ATTENDANCE_FILE) else pd.DataFrame(columns=["Name", "Date", "Time", "Type"])
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        today_records = df[(df["Name"] == name) & (df["Date"] == date)]
        record_type = "Punch-In" if len(today_records) == 0 or today_records.iloc[-1]["Type"] == "Punch-Out" else "Punch-Out"
        
        new_row = {"Name": name, "Date": date, "Time": time_str, "Type": record_type}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
        
        print(f"[{time_str}] {record_type} recorded for {name}")
        messagebox.showinfo("Attendance Marked", f"{record_type} recorded for {name} at {time_str}")
        self.stop_camera()
        self.btn_action.configure(text="Start Scanner", fg_color=["#3B8ED0", "#1F6AA5"]) # Reset button
        return record_type

if __name__ == "__main__":
    app = FaceAttendanceApp()
    app.mainloop()

import cv2
import face_recognition
import os
import pickle

name = input("Enter user name: ").strip()

SAVE_DIR = f"data/faces/{name}"
os.makedirs(SAVE_DIR, exist_ok=True)

video = cv2.VideoCapture(0)
count = 0
encodings = []

import time

print("Press 'C' once to start Burst Mode (Auto-capture 20 photos), 'Q' to quit")

while True:
    ret, frame = video.read()
    if not ret: break
    
    cv2.imshow("Register Face - Press 'C' to Start Burst", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('c') or count > 0:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb)
        face_encs = face_recognition.face_encodings(rgb, faces)

        if len(face_encs) == 1:
            encodings.append(face_encs[0])
            count += 1
            cv2.imwrite(f"{SAVE_DIR}/{count}.jpg", frame)
            print(f"Captured {count}/20")
            time.sleep(0.1)
        else:
            print("KEEP STILL - Face Lost!")

    if key == ord('q') or count >= 20:
        break

video.release()
cv2.destroyAllWindows()

# Save encodings
data = {"encodings": [], "names": []}
if os.path.exists("data/encodings.pkl") and os.path.getsize("data/encodings.pkl") > 0:
    with open("data/encodings.pkl", "rb") as f:
        try:
            old_data = pickle.load(f)
            if isinstance(old_data, dict) and "encodings" in old_data:
                data = old_data
        except EOFError:
            pass

data["encodings"].extend(encodings)
data["names"].extend([name] * len(encodings))

with open("data/encodings.pkl", "wb") as f:
    pickle.dump(data, f)

print("Face registered successfully!")

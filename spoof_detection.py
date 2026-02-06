import mediapipe as mp
import cv2
import numpy as np

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh()

LEFT_EYE = [33, 160, 158, 133, 153, 144]

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C)

def is_blink(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    if not result.multi_face_landmarks:
        return False

    h, w, _ = frame.shape
    landmarks = result.multi_face_landmarks[0].landmark

    eye = []
    for idx in LEFT_EYE:
        x = int(landmarks[idx].x * w)
        y = int(landmarks[idx].y * h)
        eye.append((x, y))

    ear = eye_aspect_ratio(np.array(eye))
    return ear < 0.2  # Blink threshold

import random
import cv2
import hashlib
import numpy as np
from scipy.spatial import distance as dist

CHALLENGES = ["blink", "turn_left", "turn_right"]

class LivenessDetector:
    def __init__(self):
        self.challenge = random.choice(CHALLENGES)
        self.blink_counter = 0
        self.prev_frame = None
        self.recent_hashes = set()

    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)

    def detect_motion(self, frame):
        if self.prev_frame is None:
            self.prev_frame = frame
            return True

        diff = cv2.absdiff(self.prev_frame, frame)
        motion_score = diff.mean()
        self.prev_frame = frame

        return motion_score > 2.0   # blocks photos/screenshots

    def detect_replay(self, frame):
        frame_hash = hashlib.md5(frame.tobytes()).hexdigest()
        if frame_hash in self.recent_hashes:
            return False
        self.recent_hashes.add(frame_hash)
        if len(self.recent_hashes) > 10:
            self.recent_hashes.clear()
        return True

    def verify_challenge(self, landmark, frame_width):
        """ Returns True if challenge is currently being met """
        if self.challenge == "blink":
            left = landmark["left_eye"]
            right = landmark["right_eye"]
            ear = (self.eye_aspect_ratio(left) + self.eye_aspect_ratio(right)) / 2
            # Threshold adjusted for better sensitivity
            return ear < 0.22 

        # For head turns, we use the nose position relative to the jawline (chin)
        # Jawline points: 0 is far left, 16 is far right
        chin = landmark["chin"]
        nose = landmark["nose_tip"][0]
        
        face_left = chin[0][0]
        face_right = chin[16][0]
        face_width = face_right - face_left
        
        if face_width == 0: return False
        
        # Calculate where the nose is relative to the face width (0 to 1.0)
        # 0.5 is centered, <0.4 is left, >0.6 is right
        ratio = (nose[0] - face_left) / face_width

        if self.challenge == "turn_left":
            return ratio < 0.35 # Nose is far left relative to jaw

        if self.challenge == "turn_right":
            return ratio > 0.65 # Nose is far right relative to jaw

        return False

    def next_challenge(self):
        """ Rotate to a different challenge """
        self.challenge = random.choice([c for c in CHALLENGES if c != self.challenge])

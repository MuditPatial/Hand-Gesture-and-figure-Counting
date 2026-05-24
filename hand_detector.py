"""
Hand Gesture Detector — Core Module
====================================
Uses MediaPipe Tasks API (HandLandmarker) to detect hand landmarks,
count raised fingers, and recognize named gestures.
Reusable by both the standalone script (main.py) and web server (app.py).
"""

import os
import cv2
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarksConnections,
    RunningMode,
)


class HandDetector:
    """Detects hands, counts fingers, and recognizes gestures."""

    # Fingertip landmark IDs (MediaPipe hand model)
    TIP_IDS = [4, 8, 12, 16, 20]   # Thumb, Index, Middle, Ring, Pinky

    # PIP/IP joint IDs (comparison reference for each finger)
    PIP_IDS = [3, 6, 10, 14, 18]   # Thumb-IP, Index-PIP, Middle-PIP, Ring-PIP, Pinky-PIP

    # MCP joint IDs (lower knuckle — used for extra gesture checks)
    MCP_IDS = [2, 5,  9, 13, 17]

    FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

    # Drawing colours (BGR)
    LANDMARK_COLOR  = (180, 60, 255)   # violet
    TIP_COLOR       = (255, 50, 150)   # pink-magenta for tips
    CONNECTION_COLOR= (0, 200, 255)    # cyan
    COUNT_COLOR     = (50, 255, 120)   # bright green
    GESTURE_COLOR   = (0, 220, 255)    # amber-yellow

    MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

    def __init__(self, max_hands=2, detection_confidence=0.7, tracking_confidence=0.5):
        self.max_hands = max_hands

        if not os.path.exists(self.MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found: {self.MODEL_PATH}\n"
                "Download it with:\n"
                '  Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/'
                'hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" '
                '-OutFile "hand_landmarker.task"'
            )

        base_options = python.BaseOptions(model_asset_path=self.MODEL_PATH)
        options = HandLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.IMAGE,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.hand_connections = HandLandmarksConnections.HAND_CONNECTIONS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame, flipped=False):
        """
        Detect hands and count fingers in a single BGR frame.

        Args:
            frame:   BGR numpy array (from OpenCV).
            flipped: True if the frame was horizontally flipped before
                     calling detect (mirror mode). Corrects hand labels
                     and thumb direction.

        Returns dict with:
            'total_fingers' : int  (0-10)
            'hands'         : list of hand dicts, each containing:
                                'label'        – corrected 'Left'/'Right'
                                'finger_count' – int 0-5
                                'fingers_up'   – [bool x5]
                                'gesture'      – gesture name string
                                'gesture_emoji'– emoji string
                                'landmarks'    – [(px,py) x21]
                                'confidence'   – float
            'annotated_frame': frame with drawings
        """
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results   = self.landmarker.detect(mp_image)

        annotated     = frame.copy()
        hand_data     = []
        total_fingers = 0

        if results.hand_landmarks and results.handedness:
            for hand_landmarks, handedness_info in zip(
                results.hand_landmarks, results.handedness
            ):
                # Raw label MediaPipe gives (inverted when frame is mirrored)
                mp_label   = handedness_info[0].category_name   # 'Left' or 'Right'
                confidence = handedness_info[0].score

                # Corrected label shown to the user
                # When flipped: MediaPipe sees a mirror image, so labels are inverted
                display_label = ("Right" if mp_label == "Left" else "Left") if flipped else mp_label

                # Pixel coords for all 21 landmarks
                landmarks_px = [
                    (int(lm.x * w), int(lm.y * h))
                    for lm in hand_landmarks
                ]

                # Finger state using raw mp_label (thumb X-logic depends on image orientation)
                fingers_up  = self._count_fingers(hand_landmarks, mp_label, flipped)
                finger_count = sum(fingers_up)
                total_fingers += finger_count

                # Gesture recognition
                gesture_name, gesture_emoji = self._recognize_gesture(
                    fingers_up, hand_landmarks, display_label
                )

                hand_data.append({
                    "label":        display_label,
                    "finger_count": finger_count,
                    "fingers_up":   fingers_up,
                    "gesture":      gesture_name,
                    "gesture_emoji":gesture_emoji,
                    "landmarks":    landmarks_px,
                    "confidence":   round(confidence, 2),
                })

                # Draw skeleton + label on frame
                self._draw_hand(
                    annotated, landmarks_px, finger_count,
                    display_label, gesture_name
                )

        self._draw_total_count(annotated, total_fingers, len(hand_data))
        return {
            "total_fingers":  total_fingers,
            "hands":          hand_data,
            "annotated_frame":annotated,
        }

    # ------------------------------------------------------------------
    # Finger counting
    # ------------------------------------------------------------------

    def _count_fingers(self, hand_landmarks, mp_label, flipped=False):
        """
        Returns [bool x5] for [Thumb, Index, Middle, Ring, Pinky].

        Uses mp_label (the raw MediaPipe label before flipping correction)
        because the landmark X-coordinates still reflect the actual image
        pixel positions after flipping.
        """
        lm = hand_landmarks
        fingers_up = []

        # ---- Thumb (lateral movement → compare X) ----
        thumb_tip = lm[self.TIP_IDS[0]]
        thumb_ip  = lm[self.PIP_IDS[0]]

        if flipped:
            # Mirrored image: both label and thumb X-direction are inverted
            if mp_label == "Right":
                fingers_up.append(thumb_tip.x > thumb_ip.x)
            else:
                fingers_up.append(thumb_tip.x < thumb_ip.x)
        else:
            if mp_label == "Right":
                fingers_up.append(thumb_tip.x < thumb_ip.x)
            else:
                fingers_up.append(thumb_tip.x > thumb_ip.x)

        # ---- Index → Pinky (vertical: tip above PIP) ----
        for i in range(1, 5):
            tip = lm[self.TIP_IDS[i]]
            pip = lm[self.PIP_IDS[i]]
            fingers_up.append(tip.y < pip.y)

        return fingers_up

    # ------------------------------------------------------------------
    # Gesture recognition
    # ------------------------------------------------------------------

    def _recognize_gesture(self, fingers_up, hand_landmarks, display_label):
        """
        Map finger state + landmark geometry to a named gesture.

        Returns (gesture_name: str, emoji: str)
        """
        lm = hand_landmarks
        t, i, m, r, p = fingers_up          # thumb, index, middle, ring, pinky
        count = sum(fingers_up)

        # Helper: normalised distance between two landmark indices
        def dist(a, b):
            dx = lm[a].x - lm[b].x
            dy = lm[a].y - lm[b].y
            return (dx*dx + dy*dy) ** 0.5

        # ── 0 fingers ──────────────────────────────────────────────────
        if count == 0:
            return "Fist", "FIST"

        # ── 1 finger ───────────────────────────────────────────────────
        if count == 1:
            if t:
                # Thumb direction: wrist-to-thumb-tip vertical component
                # positive y means downward in image space
                wrist_y = lm[0].y
                tip_y   = lm[4].y
                if tip_y < wrist_y - 0.05:
                    return "Thumbs Up", "THUMBS_UP"
                elif tip_y > wrist_y + 0.05:
                    return "Thumbs Down", "THUMBS_DOWN"
                else:
                    return "Thumb Out", "THUMB_OUT"
            if i:  return "Point / One",  "ONE"
            if m:  return "Middle Finger","MIDDLE"
            if r:  return "Ring Up",       "RING"
            if p:  return "Pinky Up",      "PINKY"

        # ── 2 fingers ──────────────────────────────────────────────────
        if count == 2:
            if i and m:  return "Peace / Two",    "PEACE"
            if t and i:  return "Finger Gun",      "GUN"
            if t and p:  return "Hang Loose",      "HANG_LOOSE"
            if r and p:  return "Two",             "TWO"
            return "Two", "TWO"

        # ── 3 fingers ──────────────────────────────────────────────────
        if count == 3:
            if i and m and r:  return "Three",       "THREE"
            if t and i and p:  return "Rock On",      "ROCK_ON"
            if t and i and m:  return "Three (Guns)", "THREE"
            return "Three", "THREE"

        # ── 4 fingers ──────────────────────────────────────────────────
        if count == 4:
            if not t:  return "Four",  "FOUR"
            if not p:  return "Four",  "FOUR"
            return "Four", "FOUR"

        # ── 5 fingers ──────────────────────────────────────────────────
        if count == 5:
            # Check "OK" sign: thumb tip close to index tip, others open
            if dist(4, 8) < 0.06:
                return "OK Sign", "OK"
            return "Open Palm / Five", "FIVE"

        return "Unknown", "UNKNOWN"

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_hand(self, frame, landmarks_px, finger_count, display_label, gesture_name):
        """Draw skeleton, fingertip markers, and label on the frame."""

        # Connections
        for connection in self.hand_connections:
            s = landmarks_px[connection.start]
            e = landmarks_px[connection.end]
            cv2.line(frame, s, e, self.CONNECTION_COLOR, 2, cv2.LINE_AA)

        # Landmark points
        for idx, (px, py) in enumerate(landmarks_px):
            if idx in self.TIP_IDS:
                cv2.circle(frame, (px, py), 8, self.TIP_COLOR, cv2.FILLED)
                cv2.circle(frame, (px, py), 8, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (px, py), 4, self.LANDMARK_COLOR, cv2.FILLED)

        # Label near the wrist
        wrist = landmarks_px[0]
        label_text   = f"{display_label}: {finger_count}"
        gesture_text = gesture_name

        for text, offset_y, color in [
            (label_text,   +18, self.COUNT_COLOR),
            (gesture_text, +42, self.GESTURE_COLOR),
        ]:
            ts = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)[0]
            rx = max(0, wrist[0] - 6)
            ry = wrist[1] + offset_y
            # dark background
            cv2.rectangle(frame,
                          (rx - 4, ry - ts[1] - 4),
                          (rx + ts[0] + 8, ry + 6),
                          (0, 0, 0), cv2.FILLED)
            cv2.putText(frame, text, (rx, ry),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)

    def _draw_total_count(self, frame, total_fingers, num_hands):
        """Draw large finger count in the top-left corner."""
        # Background box
        cv2.rectangle(frame, (8, 8), (188, 130), (0, 0, 0), cv2.FILLED)
        cv2.rectangle(frame, (8, 8), (188, 130), self.LANDMARK_COLOR, 2)

        # Big digit
        cv2.putText(frame, str(total_fingers),
                    (45, 95), cv2.FONT_HERSHEY_SIMPLEX, 3.0, self.COUNT_COLOR, 5)
        cv2.putText(frame, "Fingers Detected",
                    (13, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)
        cv2.putText(frame, f"Hands: {num_hands}",
                    (13, 148), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    def release(self):
        """Release MediaPipe resources."""
        self.landmarker.close()

"""
Hand Gesture Detector — Core Module
====================================
Uses MediaPipe Tasks API (HandLandmarker) to detect hand landmarks
and count raised fingers.
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
    drawing_utils,
)


class HandDetector:
    """Detects hands and counts raised fingers using MediaPipe Tasks API."""

    # Fingertip landmark IDs (MediaPipe hand model)
    TIP_IDS = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky

    # Corresponding PIP/IP joint IDs (one step below the tip for comparison)
    PIP_IDS = [3, 6, 10, 14, 18]  # Thumb IP, Index PIP, Middle PIP, Ring PIP, Pinky PIP

    # Finger names for display
    FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

    # Custom drawing styles
    LANDMARK_COLOR = (138, 43, 226)   # Blue-violet (BGR)
    CONNECTION_COLOR = (255, 165, 0)  # Orange (BGR)
    COUNT_COLOR = (0, 255, 128)       # Green (BGR)

    # Path to the model file (relative to this script)
    MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

    def __init__(self, max_hands=2, detection_confidence=0.7, tracking_confidence=0.5):
        """
        Initialize the hand detector.

        Args:
            max_hands: Maximum number of hands to detect (1 or 2).
            detection_confidence: Minimum confidence for hand detection.
            tracking_confidence: Minimum confidence for hand tracking.
        """
        self.max_hands = max_hands

        if not os.path.exists(self.MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found: {self.MODEL_PATH}\n"
                "Download it with:\n"
                '  Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/'
                'hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" '
                '-OutFile "hand_landmarker.task"'
            )

        # Configure the HandLandmarker using the Tasks API
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

        # Hand connections for drawing
        self.hand_connections = HandLandmarksConnections.HAND_CONNECTIONS

    def detect(self, frame, flipped=False):
        """
        Detect hands and count fingers in a single frame.

        Args:
            frame: BGR image (numpy array from OpenCV).
            flipped: True if the frame was horizontally flipped before calling
                     detect. This affects thumb direction logic.

        Returns:
            dict with keys:
                - 'total_fingers': int (0–10)
                - 'hands': list of dicts per hand, each with:
                    - 'label': 'Left' or 'Right'
                    - 'finger_count': int (0–5)
                    - 'fingers_up': list of 5 bools [thumb, index, middle, ring, pinky]
                    - 'landmarks': list of (x, y) pixel coords for 21 landmarks
                    - 'confidence': float detection confidence
                - 'annotated_frame': frame with landmarks drawn on it
        """
        h, w, _ = frame.shape

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Run detection
        results = self.landmarker.detect(mp_image)

        annotated = frame.copy()
        hand_data = []
        total_fingers = 0

        if results.hand_landmarks and results.handedness:
            for hand_landmarks, handedness_info in zip(
                results.hand_landmarks, results.handedness
            ):
                # --- Extract handedness ---
                label = handedness_info[0].category_name  # 'Left' or 'Right'
                confidence = handedness_info[0].score

                # --- Get pixel coordinates for all 21 landmarks ---
                landmarks_px = []
                for lm in hand_landmarks:
                    px = int(lm.x * w)
                    py = int(lm.y * h)
                    landmarks_px.append((px, py))

                # --- Count raised fingers ---
                fingers_up = self._count_fingers(hand_landmarks, label, flipped)
                finger_count = sum(fingers_up)
                total_fingers += finger_count

                hand_data.append({
                    "label": label,
                    "finger_count": finger_count,
                    "fingers_up": fingers_up,
                    "landmarks": landmarks_px,
                    "confidence": round(confidence, 2),
                })

                # --- Draw landmarks on frame ---
                self._draw_hand(annotated, hand_landmarks, landmarks_px, finger_count, label, h, w)

        # --- Draw total count overlay ---
        self._draw_total_count(annotated, total_fingers, len(hand_data))

        return {
            "total_fingers": total_fingers,
            "hands": hand_data,
            "annotated_frame": annotated,
        }

    def _count_fingers(self, hand_landmarks, hand_label, flipped=False):
        """
        Determine which fingers are raised.

        When the frame is flipped (mirrored), MediaPipe's handedness label
        gets inverted AND the thumb X-direction flips. We swap the thumb
        comparison to compensate.

        Returns:
            List of 5 booleans: [thumb, index, middle, ring, pinky]
        """
        lm = hand_landmarks
        fingers_up = []

        # --- Thumb ---
        # The thumb moves laterally, so we compare X-coordinates.
        # When flipped, both handedness and thumb direction are mirrored,
        # so we swap the comparison operator.
        thumb_tip = lm[self.TIP_IDS[0]]
        thumb_ip = lm[self.PIP_IDS[0]]

        if flipped:
            # Frame is mirrored: swap thumb logic
            if hand_label == "Right":
                fingers_up.append(thumb_tip.x > thumb_ip.x)
            else:
                fingers_up.append(thumb_tip.x < thumb_ip.x)
        else:
            # Normal (non-flipped) frame
            if hand_label == "Right":
                fingers_up.append(thumb_tip.x < thumb_ip.x)
            else:
                fingers_up.append(thumb_tip.x > thumb_ip.x)

        # --- Index, Middle, Ring, Pinky ---
        # A finger is raised if its tip is ABOVE (lower y-value) its PIP joint
        # Y-direction is NOT affected by horizontal flip
        for i in range(1, 5):
            tip = lm[self.TIP_IDS[i]]
            pip = lm[self.PIP_IDS[i]]
            fingers_up.append(tip.y < pip.y)

        return fingers_up

    def _draw_hand(self, frame, hand_landmarks, landmarks_px, finger_count, label, h, w):
        """Draw hand skeleton and per-hand info on the frame."""

        # Draw connections manually (lines between connected landmarks)
        for connection in self.hand_connections:
            start_idx = connection.start
            end_idx = connection.end
            start_pt = landmarks_px[start_idx]
            end_pt = landmarks_px[end_idx]
            cv2.line(frame, start_pt, end_pt, self.CONNECTION_COLOR, 2, cv2.LINE_AA)

        # Draw landmark points
        for idx, (px, py) in enumerate(landmarks_px):
            # Fingertips get a larger circle
            if idx in self.TIP_IDS:
                cv2.circle(frame, (px, py), 7, self.LANDMARK_COLOR, cv2.FILLED)
                cv2.circle(frame, (px, py), 7, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, (px, py), 4, self.LANDMARK_COLOR, cv2.FILLED)

        # Draw per-hand finger count near the wrist
        wrist = landmarks_px[0]
        label_text = f"{label}: {finger_count}"

        # Background rectangle for readability
        text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        rect_x = wrist[0] - 10
        rect_y = wrist[1] + 10
        cv2.rectangle(
            frame,
            (rect_x, rect_y),
            (rect_x + text_size[0] + 20, rect_y + text_size[1] + 15),
            (0, 0, 0),
            cv2.FILLED,
        )
        cv2.rectangle(
            frame,
            (rect_x, rect_y),
            (rect_x + text_size[0] + 20, rect_y + text_size[1] + 15),
            self.LANDMARK_COLOR,
            2,
        )
        cv2.putText(
            frame,
            label_text,
            (rect_x + 10, rect_y + text_size[1] + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            self.COUNT_COLOR,
            2,
        )

    def _draw_total_count(self, frame, total_fingers, num_hands):
        """Draw the total finger count as a large overlay in the top-left corner."""
        h, w, _ = frame.shape

        # Main count display
        count_text = str(total_fingers)
        label_text = "Fingers Detected"

        # Large count number
        cv2.rectangle(frame, (10, 10), (180, 120), (0, 0, 0), cv2.FILLED)
        cv2.rectangle(frame, (10, 10), (180, 120), self.LANDMARK_COLOR, 2)

        cv2.putText(
            frame, count_text, (50, 90),
            cv2.FONT_HERSHEY_SIMPLEX, 2.5, self.COUNT_COLOR, 4,
        )
        cv2.putText(
            frame, label_text, (15, 112),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1,
        )

        # Hands detected indicator
        hands_text = f"Hands: {num_hands}"
        cv2.putText(
            frame, hands_text, (15, 145),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1,
        )

    def release(self):
        """Release MediaPipe resources."""
        self.landmarker.close()

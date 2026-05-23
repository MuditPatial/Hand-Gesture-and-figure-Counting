"""
Hand Gesture Recognition — Standalone Mode
=============================================
Run this script to use hand gesture recognition directly with OpenCV
without starting the web server. Press 'q' to quit.

Usage:
    python main.py
"""

import cv2
import sys
import time
from hand_detector import HandDetector


def main():
    """Run the standalone hand gesture recognizer."""
    print("=" * 55)
    print("  Hand Gesture Recognition - Standalone Mode")
    print("=" * 55)
    print()

    # Initialize the hand detector
    detector = HandDetector(max_hands=2, detection_confidence=0.7, tracking_confidence=0.5)

    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        print("   Make sure your camera is connected and not in use by another app.")
        sys.exit(1)

    # Set camera resolution for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("[OK] Webcam opened successfully!")
    print("  Show your hand(s) to the camera.")
    print("  The number of raised fingers will be displayed.")
    print("  Press 'q' to quit.\n")

    # FPS tracking
    prev_time = time.time()
    fps = 0

    while True:
        success, frame = cap.read()
        if not success:
            print("[ERROR] Failed to read from webcam.")
            break

        # Flip frame horizontally for a mirror-like experience
        frame = cv2.flip(frame, 1)

        # Detect hands and count fingers
        result = detector.detect(frame, flipped=True)
        annotated = result["annotated_frame"]

        # Calculate and display FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time
        cv2.putText(
            annotated,
            f"FPS: {int(fps)}",
            (annotated.shape[1] - 130, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 128),
            2,
        )

        # Print finger details to console (throttled)
        if result["hands"]:
            for hand in result["hands"]:
                finger_status = []
                for i, (name, is_up) in enumerate(
                    zip(HandDetector.FINGER_NAMES, hand["fingers_up"])
                ):
                    finger_status.append(f"{name}: {'UP' if is_up else 'DN'}")
                status_line = " | ".join(finger_status)
                # Only print occasionally to avoid flooding
                if int(curr_time * 2) % 2 == 0:
                    print(
                        f"\r  {hand['label']} hand: {hand['finger_count']} fingers "
                        f"[{status_line}]   ",
                        end="",
                    )

        # Show the annotated frame
        cv2.imshow("Hand Gesture Recognition", annotated)

        # Quit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q or ESC
            break

    # Cleanup
    print("\n\nShutting down...")
    cap.release()
    cv2.destroyAllWindows()
    detector.release()
    print("[OK] Done. Goodbye!")


if __name__ == "__main__":
    main()

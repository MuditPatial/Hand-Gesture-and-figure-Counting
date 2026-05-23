"""
Hand Gesture Recognition — Web Server
========================================
Flask + SocketIO web server that streams hand gesture detection
via WebSockets. Run this to start the web interface.

Usage:
    python app.py
    Then open http://localhost:5000 in your browser.
"""

import base64
import cv2
import numpy as np
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit

from hand_detector import HandDetector

# --- Flask App Setup ---
app = Flask(__name__)
app.config["SECRET_KEY"] = "hand-gesture-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --- Hand Detector (shared across connections) ---
detector = HandDetector(max_hands=2, detection_confidence=0.7, tracking_confidence=0.5)


# =============================================================================
# Routes
# =============================================================================

@app.route("/")
def index():
    """Serve the main web interface."""
    return render_template("index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static files."""
    return send_from_directory("static", filename)


# =============================================================================
# WebSocket Events
# =============================================================================

@socketio.on("connect")
def handle_connect():
    """Handle new client connection."""
    print("[+] Client connected")
    emit("status", {"message": "Connected to Hand Gesture Server"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    print("[-] Client disconnected")


@socketio.on("video_frame")
def handle_video_frame(data):
    """
    Process a video frame from the client.

    Receives: base64-encoded JPEG image
    Emits: processed frame + detection results
    """
    try:
        # --- Decode base64 frame ---
        # The data comes as "data:image/jpeg;base64,<actual_data>"
        if "," in data:
            encoded = data.split(",")[1]
        else:
            encoded = data

        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return

        # --- Flip frame for mirror effect ---
        frame = cv2.flip(frame, 1)

        # --- Run hand detection ---
        result = detector.detect(frame, flipped=True)

        # --- Encode annotated frame back to base64 JPEG ---
        _, buffer = cv2.imencode(".jpg", result["annotated_frame"], [cv2.IMWRITE_JPEG_QUALITY, 80])
        annotated_b64 = base64.b64encode(buffer).decode("utf-8")

        # --- Build response ---
        hands_info = []
        for hand in result["hands"]:
            hands_info.append({
                "label": hand["label"],
                "finger_count": hand["finger_count"],
                "fingers_up": hand["fingers_up"],
                "confidence": hand["confidence"],
            })

        response = {
            "frame": f"data:image/jpeg;base64,{annotated_b64}",
            "total_fingers": result["total_fingers"],
            "hands": hands_info,
            "num_hands": len(result["hands"]),
        }

        emit("processed_frame", response)

    except Exception as e:
        print(f"[!] Error processing frame: {e}")
        emit("error", {"message": str(e)})


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  Hand Gesture Recognition - Web Server")
    print("=" * 55)
    print()
    print("  Starting server at http://localhost:5000")
    print("  Open the URL in your browser to begin.")
    print("  Press Ctrl+C to stop.\n")

    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)


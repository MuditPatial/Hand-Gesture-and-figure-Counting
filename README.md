# 🖐️ Hand Gesture Recognition — Finger Counter

<div align="center">

**Real-time hand gesture recognition that counts your raised fingers using AI-powered computer vision.**

Show ✌️ → It says **2**. Show 🖐️ → It says **5**. Show ✊ → It says **0**.

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-00897B?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)

</div>

---

## ✨ Features

- 🔢 **Finger Counting (0–10)** — Accurately counts raised fingers on one or two hands
- 🖐️ **Two-Hand Support** — Detects and tracks up to 2 hands simultaneously
- 🏷️ **Gesture Labels** — Recognizes common gestures (Peace ✌️, Thumbs Up 👍, Fist ✊, etc.)
- 🌐 **Web Interface** — Beautiful dark-themed UI with real-time webcam streaming
- 🖥️ **Standalone Mode** — Run directly with OpenCV, no browser needed
- ⚡ **Real-Time** — ~15 FPS processing with live skeleton overlay
- 🎨 **Premium UI** — Glassmorphic design with animations and per-finger indicators

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser (Web UI)                  │
│  ┌──────────┐  WebSocket   ┌───────────────────┐    │
│  │  Webcam  │ ───────────> │  Flask-SocketIO   │    │
│  │  Feed    │ <─────────── │  Server (app.py)  │    │
│  └──────────┘  Annotated   └────────┬──────────┘    │
│                  Frame              │               │
│                            ┌───────┴────────┐       │
│                            │ HandDetector   │       │
│                            │ (MediaPipe)    │       │
│                            └────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### How Finger Counting Works

The system uses **MediaPipe Hands** to detect **21 landmarks** on each hand:

```
         8   12  16  20       ← Fingertips
         |   |   |   |
     4   7   11  15  19       ← DIP joints
     |   |   |   |   |
     3   6   10  14  18       ← PIP joints (comparison points)
     |   |   |   |   |
     2   5   9   13  17       ← MCP joints
      \  |   |   |  /
       \ |   |   | /
        \|   |   |/
         1───┼───┘
         |   |
         0   ← Wrist
```

**Detection Logic:**
- **Index / Middle / Ring / Pinky:** Finger is "up" if its **tip Y-coordinate < PIP Y-coordinate** (tip is above the knuckle in image space)
- **Thumb:** Uses **X-coordinate** comparison since the thumb moves laterally. Direction depends on whether it's the left or right hand (determined via `results.multi_handedness`)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Webcam** (built-in or USB)
- **pip** (Python package manager)

### Installation

```bash
# 1. Clone or navigate to the project directory
cd "Hand Gesture"

# 2. (Optional) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

### Run — Web Interface (Recommended)

```bash
python app.py
```

Then open **http://localhost:5000** in your browser and click **"Start Camera"**.

### Run — Standalone Mode (No Browser)

```bash
python main.py
```

An OpenCV window will open with your webcam feed. Press **`q`** to quit.

---

## 📁 Project Structure

```
Hand Gesture/
├── app.py                  # Flask + SocketIO web server
├── main.py                 # Standalone OpenCV script
├── hand_detector.py        # Core detection module (MediaPipe)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── templates/
│   └── index.html          # Web interface HTML
└── static/
    ├── css/
    │   └── style.css       # Dark glassmorphic theme
    └── js/
        └── app.js          # WebSocket + webcam logic
```

---

## 🎮 Usage Guide

| Gesture | Fingers | What You'll See |
|---------|---------|-----------------|
| ✊ Fist | 0 | `0` — "Fist" |
| ☝️ Point | 1 | `1` — "One / Point" |
| ✌️ Peace | 2 | `2` — "Peace / Two" |
| 3 Fingers | 3 | `3` — "Three" |
| 4 Fingers | 4 | `4` — "Four" |
| 🖐️ Open Palm | 5 | `5` — "Open Palm / Five" |
| 👍 Thumbs Up | 1 | `1` — "Thumbs Up" |
| 🤟 ILY | 3 | `3` — "Rock On" |
| 🙌 Both Open | 10 | `10` — "All Ten!" |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Hand Detection | [MediaPipe Hands](https://google.github.io/mediapipe/solutions/hands.html) |
| Image Processing | [OpenCV](https://opencv.org/) |
| Web Server | [Flask](https://flask.palletsprojects.com/) + [Flask-SocketIO](https://flask-socketio.readthedocs.io/) |
| Real-Time Comm | WebSockets via [Socket.IO](https://socket.io/) |
| Frontend | HTML5, CSS3 (Glassmorphism), JavaScript |
| Async Runtime | [Eventlet](https://eventlet.net/) |

---

## ⚙️ Configuration

You can adjust detection parameters in `hand_detector.py` or when creating the `HandDetector` instance:

```python
detector = HandDetector(
    max_hands=2,                # 1 or 2 hands
    detection_confidence=0.7,   # 0.0–1.0, higher = stricter
    tracking_confidence=0.5,    # 0.0–1.0, higher = stricter
)
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not opening | Make sure no other app is using the webcam |
| Low FPS | Reduce frame size or increase capture interval in `app.js` |
| Thumb detection inaccurate | Ensure good lighting and keep your hand facing the camera |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Browser shows "Camera blocked" | Allow camera permissions in your browser settings |

---

## 📜 License

This project is open source under the [MIT License](https://opensource.org/licenses/MIT).

---

<div align="center">
  <p>Built with ❤️ using MediaPipe, OpenCV & Flask</p>
</div>

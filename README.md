# Hand Gesture Recognition — Finger Counter

<div align="center">

**Real-time hand gesture recognition that counts your raised fingers using AI-powered computer vision.**

Show ✌️ → It says **2**. Show 🖐️ → It says **5**. Show 👍 → It says **Thumbs Up**.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10+-00897B?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)

</div>

---

## What This Project Does

This project uses your **webcam** to detect hand gestures in real time. It can:
- Count how many fingers you are holding up (0 to 10)
- Recognize named gestures like Thumbs Up, Peace sign, Rock On, etc.
- Show a live skeleton overlay on your hand
- Work in a browser (web mode) or directly in a window (standalone mode)

---

## Features

- **Finger Counting (0–10)** — Accurately counts raised fingers on one or two hands
- **Two-Hand Support** — Detects and tracks up to 2 hands simultaneously
- **15+ Gesture Labels** — Peace, Thumbs Up/Down, Fist, Finger Gun, Rock On, OK Sign, and more
- **Web Interface** — Dark-themed UI with real-time webcam streaming
- **Standalone Mode** — Run directly with OpenCV, no browser needed
- **Works Offline** — All AI models and libraries run locally on your machine
- **Share Online** — Use ngrok to share with anyone in the world instantly

---

## How It Works (Simple Explanation)

```
Your Webcam
    |
    | (video frames)
    v
Flask Server (app.py)
    |
    | (runs AI on each frame)
    v
MediaPipe AI  -->  detects 21 points on your hand
    |
    | (counts which fingers are up)
    v
Result sent back to your Browser
```

The AI detects **21 landmark points** on your hand. A finger is counted as "up" if its tip is higher than its knuckle.

---

## Project Files Explained

```
Hand Gesture/
├── app.py              ← Main web server (run this for the website)
├── main.py             ← Standalone mode (no browser needed)
├── hand_detector.py    ← The AI brain — detects hands and counts fingers
├── hand_landmarker.task← The AI model file (downloaded automatically)
├── requirements.txt    ← List of Python packages needed
├── Dockerfile          ← For Docker/cloud deployment
├── Procfile            ← For Railway/Render cloud deployment
├── README.md           ← This file
├── templates/
│   └── index.html      ← The webpage
└── static/
    ├── css/style.css   ← Styling for the webpage
    └── js/app.js       ← Webcam + live update logic
```

---

## Installation (First Time Setup)

**You only need to do this once.**

### Step 1 — Make sure Python is installed

Open PowerShell and type:
```powershell
python --version
```
You should see something like `Python 3.10.x`. If not, download Python from [python.org](https://python.org).

### Step 2 — Navigate to the project folder

```powershell
cd "C:\Users\patia\Desktop\Deep Learning\Hand Gesture"
```

### Step 3 — Install the required packages

```powershell
pip install -r requirements.txt
```

This installs OpenCV, MediaPipe, Flask, and everything else the project needs. It may take a few minutes.

---

## Running the App

### Option A — Web Mode (Recommended)

This opens a website in your browser with a nice UI.

**Start the server:**
```powershell
python app.py
```

You will see:
```
=======================================================
  Hand Gesture Recognition - Web Server
=======================================================

  Starting server at http://localhost:5000
  Open the URL in your browser to begin.
  Press Ctrl+C to stop.
```

**Open your browser** and go to: **http://localhost:5000**

Click **"Start Camera"** and show your hand!

**To stop:** Press `Ctrl + C` in the PowerShell window.

---

### Option B — Standalone Mode (No Browser)

This opens a plain OpenCV window — simpler, good for testing.

```powershell
python main.py
```

An OpenCV window will open showing your webcam with the hand skeleton overlay.

**To stop:** Press `q` on your keyboard while the window is focused.

---

## Gestures Recognized

| Gesture | Fingers Up | What the App Shows |
|---------|-----------|-------------------|
| ✊ Fist | 0 | "Fist" |
| 👍 Thumbs Up | thumb only, pointing up | "Thumbs Up" |
| 👎 Thumbs Down | thumb only, pointing down | "Thumbs Down" |
| ☝️ Point | index only | "Point / One" |
| ✌️ Peace | index + middle | "Peace / Two" |
| 🤜 Finger Gun | thumb + index | "Finger Gun" |
| 🤙 Hang Loose | thumb + pinky | "Hang Loose / Shaka" |
| 3️⃣ Three | index + middle + ring | "Three" |
| 🤘 Rock On | thumb + index + pinky | "Rock On" |
| 4️⃣ Four | all except thumb | "Four" |
| 👌 OK Sign | all 5 (thumb near index) | "OK Sign" |
| 🖐️ Open Palm | all 5 fingers | "Open Palm / Five" |
| 🙌 Both Hands Open | 10 fingers | "All Ten! High Five!" |

---

## Sharing With Others (ngrok)

By default the app only works on **your own computer** at `http://localhost:5000`.  
To share it with anyone in the world, use **ngrok** — it creates a public link.

### One-Time Setup

ngrok is already downloaded at `C:\ngrok\ngrok.exe`.

Your authtoken is already saved (if you followed setup). If you need to re-add it:
```powershell
C:\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN_HERE
```
Get your token at [dashboard.ngrok.com](https://dashboard.ngrok.com).

### Starting (Every Time)

You need **two PowerShell windows open at the same time**:

**PowerShell Window 1 — Start the Flask server:**
```powershell
cd "C:\Users\patia\Desktop\Deep Learning\Hand Gesture"
python app.py
```
Wait until you see `Running on http://127.0.0.1:5000`

**PowerShell Window 2 — Start ngrok tunnel:**
```powershell
C:\ngrok\ngrok.exe http 5000
```

ngrok will show you a public link like:
```
Forwarding    https://abc123.ngrok-free.app  ->  http://localhost:5000
```

**Share the `https://...ngrok-free.app` link** with anyone — they can open it in their browser and use your app from anywhere in the world.

### Stopping

- **Stop the Flask server:** Go to Window 1 → press `Ctrl + C`
- **Stop ngrok:** Go to Window 2 → press `Ctrl + C`

Once you press `Ctrl + C` in both windows, everything is stopped. The public link will stop working.

### Restarting

Just repeat the "Starting" steps above — open two PowerShell windows and run the same two commands. ngrok will give you a **new link** each time (the link changes every restart on the free plan).

> **Note:** Both windows must stay open while the app is running. Closing a window = stopping that process.

---

## Troubleshooting

| Problem | What to Do |
|---------|-----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Camera not opening | Make sure no other app (Zoom, Teams, etc.) is using your webcam |
| Browser shows "Camera blocked" | Click the camera icon in your browser's address bar and allow access |
| App is slow/laggy | Make sure you have good lighting — MediaPipe works faster with a clear hand |
| Thumb not counting correctly | Face your palm toward the camera, keep fingers spread apart |
| ngrok link not working | Make sure `python app.py` is also running in the other window |
| `hand_landmarker.task not found` | Delete and re-run `python app.py` — it downloads automatically |

---

## Tech Stack

| What | Technology Used |
|------|----------------|
| Hand AI Detection | [MediaPipe HandLandmarker](https://google.github.io/mediapipe/) |
| Image Processing | [OpenCV](https://opencv.org/) |
| Web Server | [Flask](https://flask.palletsprojects.com/) + [Flask-SocketIO](https://flask-socketio.readthedocs.io/) |
| Real-Time Communication | WebSockets via [Socket.IO](https://socket.io/) |
| Frontend | HTML5, CSS3 (dark glassmorphic theme), JavaScript |
| Public Sharing | [ngrok](https://ngrok.com/) |

---

## Configuration (Optional)

You can tune detection in `app.py`:

```python
detector = HandDetector(
    max_hands=2,                # Change to 1 if you only want one hand tracked
    detection_confidence=0.7,   # Higher = more accurate but may miss fast movements
    tracking_confidence=0.5,    # Higher = smoother tracking
)
```

---

<div align="center">
  <p>Built with love using MediaPipe, OpenCV & Flask</p>
  <p><em>First project — hand gesture recognition with real-time AI</em></p>
</div>

/**
 * Hand Gesture Recognition — Frontend Application
 * =================================================
 * Captures webcam frames, sends them to the Flask-SocketIO server,
 * and displays the processed results with animations.
 */

// =============================================================================
// State
// =============================================================================
let socket = null;
let videoStream = null;
let captureInterval = null;
let isRunning = false;
let lastCount = 0;
let frameCount = 0;
let fpsTimer = null;
let fps = 0;
let waitingForResponse = false; // Prevents frame pile-up

// DOM Elements
const webcamVideo = document.getElementById('webcamVideo');
const processedFrame = document.getElementById('processedFrame');
const captureCanvas = document.getElementById('captureCanvas');
const cameraOverlay = document.getElementById('cameraOverlay');
const connectionStatus = document.getElementById('connectionStatus');
const startBtn = document.getElementById('startBtn');
const totalCountEl = document.getElementById('totalCount');
const counterGlow = document.getElementById('counterGlow');
const fpsBadge = document.getElementById('fpsBadge');
const gestureEmoji = document.getElementById('gestureEmoji');
const gestureName = document.getElementById('gestureName');

// Hand cards
const leftHandCard = document.getElementById('leftHandCard');
const rightHandCard = document.getElementById('rightHandCard');
const leftHandCount = document.getElementById('leftHandCount');
const rightHandCount = document.getElementById('rightHandCount');
const leftFingers = document.getElementById('leftFingers');
const rightFingers = document.getElementById('rightFingers');

// =============================================================================
// Particles Background
// =============================================================================
function createParticles() {
    const container = document.getElementById('particles');
    const count = 40;

    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDuration = (8 + Math.random() * 12) + 's';
        particle.style.animationDelay = (Math.random() * 10) + 's';
        particle.style.width = (2 + Math.random() * 3) + 'px';
        particle.style.height = particle.style.width;

        // Random colors
        const colors = ['#8b5cf6', '#6366f1', '#3b82f6', '#22d3ee', '#34d399'];
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];

        container.appendChild(particle);
    }
}

// =============================================================================
// Socket.IO Connection
// =============================================================================
function initSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('✅ Connected to server');
        updateConnectionStatus('connected', 'Connected');
    });

    socket.on('disconnect', () => {
        console.log('❌ Disconnected from server');
        updateConnectionStatus('disconnected', 'Disconnected');
    });

    socket.on('status', (data) => {
        console.log('📡 Status:', data.message);
    });

    socket.on('processed_frame', handleProcessedFrame);

    socket.on('error', (data) => {
        console.error('⚠️ Server error:', data.message);
    });
}

function updateConnectionStatus(state, text) {
    connectionStatus.className = 'status-badge ' + state;
    connectionStatus.querySelector('.status-text').textContent = text;
}

// =============================================================================
// Camera Control
// =============================================================================
async function toggleCamera() {
    if (isRunning) {
        stopCamera();
    } else {
        await startCamera();
    }
}

async function startCamera() {
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user',
            },
            audio: false,
        });

        webcamVideo.srcObject = videoStream;
        await webcamVideo.play();

        // Set canvas size — smaller = faster processing + less data over WebSocket
        captureCanvas.width = 320;
        captureCanvas.height = 240;

        // Start capturing frames
        isRunning = true;
        waitingForResponse = false;
        captureInterval = setInterval(captureAndSend, 50); // Try ~20 FPS (server will throttle)

        // Start FPS counter
        frameCount = 0;
        fpsTimer = setInterval(() => {
            fps = frameCount;
            frameCount = 0;
            fpsBadge.textContent = fps + ' FPS';
        }, 1000);

        // Update UI
        cameraOverlay.classList.add('hidden');
        startBtn.innerHTML = '<span class="btn-icon">⏹️</span> Stop Camera';
        startBtn.classList.add('active');

        console.log('📷 Camera started');

    } catch (err) {
        console.error('❌ Camera error:', err);
        alert('Could not access camera. Please allow camera permissions and try again.');
    }
}

function stopCamera() {
    isRunning = false;

    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }

    if (fpsTimer) {
        clearInterval(fpsTimer);
        fpsTimer = null;
    }

    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }

    webcamVideo.srcObject = null;

    // Update UI
    cameraOverlay.classList.remove('hidden');
    startBtn.innerHTML = '<span class="btn-icon">▶️</span> Start Camera';
    startBtn.classList.remove('active');
    fpsBadge.textContent = '-- FPS';

    // Reset displays
    resetHandCards();
    totalCountEl.textContent = '0';
    counterGlow.classList.remove('active');
    gestureEmoji.textContent = '✊';
    gestureName.textContent = 'Camera stopped';

    console.log('📷 Camera stopped');
}

// =============================================================================
// Frame Capture & Send
// =============================================================================
function captureAndSend() {
    if (!isRunning || !socket || !socket.connected) return;
    // Don't send a new frame until the server responds to the previous one
    if (waitingForResponse) return;

    const ctx = captureCanvas.getContext('2d');
    ctx.drawImage(webcamVideo, 0, 0, captureCanvas.width, captureCanvas.height);

    const dataUrl = captureCanvas.toDataURL('image/jpeg', 0.5);
    waitingForResponse = true;
    socket.emit('video_frame', dataUrl);
}

// =============================================================================
// Handle Processed Frame
// =============================================================================
function handleProcessedFrame(data) {
    frameCount++;
    waitingForResponse = false; // Ready for next frame

    // Update the processed frame display
    processedFrame.src = data.frame;

    // Update total count with animation
    const newCount = data.total_fingers;
    if (newCount !== lastCount) {
        totalCountEl.textContent = newCount;
        totalCountEl.classList.add('bump');
        setTimeout(() => totalCountEl.classList.remove('bump'), 300);
        lastCount = newCount;
    }

    // Glow effect based on count
    if (newCount > 0) {
        counterGlow.classList.add('active');
    } else {
        counterGlow.classList.remove('active');
    }

    // Update hand cards
    updateHandCards(data.hands);

    // Update gesture
    updateGesture(data.total_fingers, data.hands);
}

// =============================================================================
// Hand Card Updates
// =============================================================================
function updateHandCards(hands) {
    // Reset both cards first
    resetHandCards();

    // Update each detected hand
    hands.forEach(hand => {
        // Note: MediaPipe mirrors labels — "Right" in results = user's left hand on screen
        // We display based on the actual label from MediaPipe
        const isLeft = hand.label === 'Left';
        const card = isLeft ? leftHandCard : rightHandCard;
        const countEl = isLeft ? leftHandCount : rightHandCount;
        const fingersEl = isLeft ? leftFingers : rightFingers;

        card.classList.add('active');
        countEl.textContent = hand.finger_count;

        // Update individual finger dots
        const fingerDivs = fingersEl.querySelectorAll('.finger');
        hand.fingers_up.forEach((isUp, idx) => {
            if (isUp) {
                fingerDivs[idx].classList.add('up');
            } else {
                fingerDivs[idx].classList.remove('up');
            }
        });
    });
}

function resetHandCards() {
    leftHandCard.classList.remove('active');
    rightHandCard.classList.remove('active');
    leftHandCount.textContent = '0';
    rightHandCount.textContent = '0';

    document.querySelectorAll('.finger').forEach(f => f.classList.remove('up'));
}

// =============================================================================
// Gesture Detection
// =============================================================================
function updateGesture(totalFingers, hands) {
    let emoji = '✊';
    let name = 'Fist';

    if (hands.length === 0) {
        emoji = '👀';
        name = 'Show your hand!';
    } else if (hands.length === 1) {
        const h = hands[0];
        const f = h.fingers_up;

        if (totalFingers === 0) {
            emoji = '✊';
            name = 'Fist';
        } else if (totalFingers === 1) {
            if (f[1]) { emoji = '☝️'; name = 'One / Point'; }
            else if (f[0]) { emoji = '👍'; name = 'Thumbs Up'; }
            else if (f[4]) { emoji = '🤙'; name = 'Pinky'; }
            else { emoji = '1️⃣'; name = 'One'; }
        } else if (totalFingers === 2) {
            if (f[1] && f[2]) { emoji = '✌️'; name = 'Peace / Two'; }
            else if (f[0] && f[4]) { emoji = '🤟'; name = 'I Love You'; }
            else if (f[0] && f[1]) { emoji = '🔫'; name = 'Finger Gun'; }
            else { emoji = '2️⃣'; name = 'Two'; }
        } else if (totalFingers === 3) {
            if (f[1] && f[2] && f[3]) { emoji = '3️⃣'; name = 'Three'; }
            else if (f[0] && f[1] && f[4]) { emoji = '🤟'; name = 'Rock On'; }
            else { emoji = '3️⃣'; name = 'Three'; }
        } else if (totalFingers === 4) {
            emoji = '4️⃣';
            name = 'Four';
        } else if (totalFingers === 5) {
            emoji = '🖐️';
            name = 'Open Palm / Five';
        }
    } else {
        // Two hands
        if (totalFingers === 0) { emoji = '👊👊'; name = 'Double Fist'; }
        else if (totalFingers === 10) { emoji = '🙌'; name = 'All Ten!'; }
        else { emoji = '🔢'; name = totalFingers + ' Fingers'; }
    }

    // Animate if changed
    if (gestureEmoji.textContent !== emoji) {
        gestureEmoji.textContent = emoji;
        gestureName.textContent = name;
        gestureEmoji.classList.add('pop');
        setTimeout(() => gestureEmoji.classList.remove('pop'), 400);
    }
}

// =============================================================================
// Initialize
// =============================================================================
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    initSocket();
});

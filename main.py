#!/usr/bin/env python3
"""
Flask + PiCamera2 Streaming and Analysis Server
------------------------------------------------
Features:
- Live video streaming from Raspberry Pi Camera
- FPS overlay
- Capture multiple frames
- Select top sharpest frames
- Robust face extraction with fallback rotations
- Save cropped faces
"""

from flask import Flask, Response, render_template_string, request, jsonify
from picamera2 import Picamera2
import cv2
import threading
import time
import os

# ---------------------------
# CONFIGURATION
# ---------------------------
CAPTURE_COUNT = 10         # Total frames to capture
TOP_N = 5                  # Number of top sharp frames to try face extraction
FALLBACK_ANGLES = [-30, 30, -15, 15]  # Rotations for robust detection

# ---------------------------
# FOLDER SETUP
# ---------------------------
os.makedirs("captured_images", exist_ok=True)
os.makedirs("best", exist_ok=True)

# ---------------------------
# FLASK APP
# ---------------------------
app = Flask(__name__)

# ---------------------------
# CAMERA SETUP
# ---------------------------
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "XRGB8888"},
    buffer_count=2
)
picam2.configure(config)
picam2.start()

latest_frame = None
frame_lock = threading.Condition()

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def save_frame(frame, folder="captured_images", prefix="frame"):
    timestamp = time.strftime("%Y%m%d-%H%M%S-%f")
    filename = f"{prefix}_{timestamp}.jpg"
    path = os.path.join(folder, filename)
    cv2.imwrite(path, frame)
    return path

def image_quality(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def rotate_image(image, angle):
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def extract_face_with_rotation(image):
    """Detect face, try fallback rotations if needed, return cropped face or None."""
    def try_detect(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return None
        x, y, w, h = faces[0]
        return img[y:y+h, x:x+w]

    face = try_detect(image)
    if face is not None:
        return face
    for angle in FALLBACK_ANGLES:
        rotated = rotate_image(image, angle)
        face = try_detect(rotated)
        if face is not None:
            return face
    return None

# ---------------------------
# CAMERA STREAM THREAD
# ---------------------------
def update_camera():
    global latest_frame
    prev_time = time.time()
    while True:
        frame = picam2.capture_array()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if curr_time-prev_time>0 else 0
            prev_time = curr_time
            cv2.putText(frame, f"FPS:{fps:.2f}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 3, cv2.LINE_AA)
            with frame_lock:
                latest_frame = frame
                frame_lock.notify_all()
        time.sleep(0.01)

def generate_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                frame_lock.wait()
                continue
            frame = latest_frame.copy()
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)

def capture_frames(count=CAPTURE_COUNT):
    frames = []
    while len(frames) < count:
        with frame_lock:
            if latest_frame is not None:
                frames.append(latest_frame.copy())
        time.sleep(0.01)
    return frames

# ---------------------------
# HTML TEMPLATE
# ---------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<title>Pi Camera Stream</title>
<style>
body { font-family: 'Segoe UI'; background:#121212; color:#E0E0E0; margin:0; }
.top-bar { display:flex; justify-content:space-between; padding:20px; }
#video { border:2px solid #333; width:400px;height:300px; background:#1E1E1E; }
button { padding:10px 20px; font-size:18px; border-radius:10px; background:#3D5AFE; color:white; border:none; cursor:pointer; margin:40px; }
button:hover { background:#5C6BC0; }
.info { padding:10px 40px; }
#status { font-weight:bold; color:#00E676; margin-bottom:8px; }
#result { background:#1E1E1E; padding:10px; border-radius:6px; font-family:monospace; white-space:pre-wrap; max-width:400px; border:1px solid #333; }
</style>
</head>
<body>
<div class="top-bar">
<img id="video" src="/video_feed" alt="Video Feed">
<button onclick="capture()">Capture & Analyze</button>
</div>
<div class="info">
<p id="status">Waiting...</p>
<div><b>Result:</b></div>
<div id="result">None</div>
</div>
<script>
function capture() {
    document.getElementById("status").innerText="Capturing...";
    document.getElementById("result").innerText="Waiting...";
    fetch("/", {method:"POST"})
        .then(r=>r.json())
        .then(data=>{
            document.getElementById("status").innerText="Done.";
            document.getElementById("result").innerText=JSON.stringify(data.result,null,2);
        })
        .catch(err=>{
            document.getElementById("status").innerText="Error.";
            console.error(err);
        });
}
</script>
</body>
</html>"""

# ---------------------------
# FLASK ROUTES
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        frames = capture_frames()
        if not frames:
            return jsonify({'result': 'Failed to capture frames'}), 500

        # Sort top N sharpest frames
        frames_sorted = sorted(frames, key=image_quality, reverse=True)[:TOP_N]

        cropped_faces = []
        for i, frame in enumerate(frames_sorted):
            face_crop = extract_face_with_rotation(frame)
            if face_crop is not None:
                path = save_frame(face_crop, folder="best", prefix=f"face_{i}")
                cropped_faces.append(os.path.basename(path))

        result = {
            "status": "success",
            "faces_saved": cropped_faces,
            "message": f"{len(cropped_faces)} faces cropped from top {TOP_N} frames."
        }
        return jsonify({'result': result})

    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ---------------------------
# MAIN
# ---------------------------
if __name__ == '__main__':
    threading.Thread(target=update_camera, daemon=True).start()
    app.run(host='0.0.0.0', port=5001, threaded=True)

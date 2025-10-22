#!/usr/bin/env python3
"""
Flask + PiCamera2 Streaming and Analysis Server
------------------------------------------------
Features:
- Live video streaming from Raspberry Pi Camera
- FPS overlay
- Capture multiple frames in a burst
- Save all captured frames in 'captured_images'
- Select top 5 sharpest frames, apply face extraction with margin & rotation
- Save best faces in 'best' folder
- Send best faces to simulated API
"""

from flask import Flask, Response, render_template_string, request, jsonify
from picamera2 import Picamera2
import cv2
import threading
import time
import os

# ---------------------------
# ⚙️ CONFIGURATION
# ---------------------------
CAPTURE_BURST_COUNT = 10          # Total frames per burst
CAPTURE_DURATION = 1.2            # Duration of burst in seconds
TOP_N = 5                         # Number of top frames to process
DEFAULT_MARGIN = 0.25             # Margin around detected face (25%)
FALLBACK_ANGLES = [-30, 30, -15, 15]  # Rotations for robust detection

# ---------------------------
# 📁 FOLDERS
# ---------------------------
os.makedirs("captured_images", exist_ok=True)
os.makedirs("best", exist_ok=True)

# ---------------------------
# 🌐 FLASK APP
# ---------------------------
app = Flask(__name__)

# ---------------------------
# 📷 CAMERA SETUP
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
# 🖼 HELPER FUNCTIONS
# ---------------------------
def save_frame(frame, folder="captured_images", prefix="frame"):
    """Save frame to disk with timestamp"""
    timestamp = time.strftime("%Y%m%d-%H%M%S-%f")
    filename = f"{prefix}_{timestamp}.jpg"
    path = os.path.join(folder, filename)
    cv2.imwrite(path, frame)
    return path

def image_quality(image):
    """Estimate image sharpness using Laplacian variance"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def get_haar_path():
    """Return Haar cascade XML path"""
    if hasattr(cv2, "data"):
        return os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    return "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

def extract_face(image, margin=DEFAULT_MARGIN):
    """
    Detect face and crop with margin.
    Returns original image if no face detected.
    """
    haar_path = get_haar_path()
    if not os.path.exists(haar_path):
        print("❌ Haar cascade not found")
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(haar_path)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        return image  # No face found

    x, y, w, h = faces[0]
    m_w, m_h = int(w * margin), int(h * margin)
    x1, y1 = max(x - m_w, 0), max(y - m_h, 0)
    x2, y2 = min(x + w + m_w, image.shape[1]), min(y + h + m_h, image.shape[0])
    return image[y1:y2, x1:x2]

def rotate_image(image, angle):
    """Rotate image around its center"""
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def extract_face_with_rotation(image, margin=DEFAULT_MARGIN, fallback_angles=FALLBACK_ANGLES):
    """
    Attempt face detection with small rotations if necessary.
    Returns cropped face or original image if none found.
    """
    # Try original
    face = extract_face(image, margin)
    if face is not image:
        return face

    # Try rotated versions
    for angle in fallback_angles:
        rotated = rotate_image(image, angle)
        face = extract_face(rotated, margin)
        if face is not rotated:
            return face

    # Fallback: return original
    return image

def send_images_to_simulated_api(image_paths):
    """Simulated API call for testing"""
    print("🔹 Simulating sending images to API...")
    for i, path in enumerate(image_paths):
        print(f"  Sending {path} as image_{i}")
    time.sleep(2)  # simulate network delay
    response = {
        "status": "success",
        "processed_images": [os.path.basename(p) for p in image_paths],
        "analysis": [{"image": os.path.basename(p), "result": "OK"} for p in image_paths]
    }
    print("🔹 Simulated API response received")
    return response

# ---------------------------
# 🖥 CAMERA STREAM THREAD
# ---------------------------
def update_camera():
    """Continuously capture latest frame for live streaming"""
    global latest_frame
    prev_time = time.time()
    while True:
        frame = picam2.capture_array()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            # Overlay FPS
            curr = time.time()
            fps = 1.0 / (curr-prev_time) if curr-prev_time>0 else 0
            prev_time = curr
            cv2.putText(frame, f"FPS:{fps:.2f}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 3, cv2.LINE_AA)
            with frame_lock:
                latest_frame = frame
                frame_lock.notify_all()
        time.sleep(0.01)

# ---------------------------
# 🌐 HTML TEMPLATE
# ---------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
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
</html>
"""

# ---------------------------
# 🌍 FLASK ROUTES
# ---------------------------
@app.route("/", methods=["GET","POST"])
def index_route():
    if request.method == "POST":
        # 1️⃣ Capture burst
        frames = []
        interval = CAPTURE_DURATION / CAPTURE_BURST_COUNT
        for _ in range(CAPTURE_BURST_COUNT):
            frame = picam2.capture_array()
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                frames.append(frame)
            time.sleep(interval)

        # 2️⃣ Save all captured frames
        [save_frame(f, folder="captured_images", prefix=f"frame_{i}") for i,f in enumerate(frames)]

        # 3️⃣ Select top N by sharpness
        frames_sorted = sorted(frames, key=image_quality, reverse=True)[:TOP_N]

        # 4️⃣ Extract faces and save best
        best_paths = []
        for i, f in enumerate(frames_sorted):
            face_img = extract_face_with_rotation(f, margin=DEFAULT_MARGIN, fallback_angles=FALLBACK_ANGLES)
            path = save_frame(face_img, folder="best", prefix=f"best_{i}")
            best_paths.append(path)

        # 5️⃣ Send to simulated API
        api_result = send_images_to_simulated_api(best_paths)

        return jsonify({"result": api_result})

    return render_template_string(HTML_TEMPLATE)

@app.route("/video_feed")
def video_feed():
    """MJPEG streaming route"""
    def generate_frames():
        global latest_frame
        while True:
            with frame_lock:
                if latest_frame is None:
                    frame_lock.wait()
                    continue
                frame = latest_frame.copy()
            _, buffer = cv2.imencode(".jpg", frame)
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
            time.sleep(0.03)
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ---------------------------
# 🚀 MAIN
# ---------------------------
if __name__ == "__main__":
    threading.Thread(target=update_camera, daemon=True).start()
    app.run(host="0.0.0.0", port=5001, threaded=True)

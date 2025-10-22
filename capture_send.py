#!/usr/bin/env python3
"""
Flask + PiCamera2 Streaming and Analysis Server
------------------------------------------------
Features:
- Live video streaming from Raspberry Pi Camera
- FPS overlay
- Capture & analyze multiple frames in a burst
- Save all captured frames to `captured_images` folder
- Select top 5 sharpest frames, save to `best` folder
- Send top frames to remote API and display response in browser
"""

from flask import Flask, Response, render_template_string, request, jsonify
from picamera2 import Picamera2
import cv2
import numpy as np
import threading
import time
import os
import requests

# ---------------------------
# ⚙️ CONFIGURATION
# ---------------------------
CAPTURE_BURST_COUNT = 10          # Number of frames to capture per burst
CAPTURE_DURATION = 1.2            # Total duration in seconds for burst
TOP_N = 5                         # Number of best frames to select
API_URL = "http://example.com/analyze"  # Replace with your API endpoint

# Create folders if they do not exist
os.makedirs("captured_images", exist_ok=True)
os.makedirs("best", exist_ok=True)

app = Flask(__name__)

# ---------------------------
# 📷 CAMERA SETUP
# ---------------------------
picam2 = Picamera2()

# Configure video: 640x480, XRGB8888 (fast & color-accurate)
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "XRGB8888"},
    buffer_count=2
)
picam2.configure(config)
picam2.start()

# Shared latest frame for streaming
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
    """Return sharpness estimate using Laplacian variance"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def rotate_image(image, angle):
    """Rotate image around its center"""
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def get_haar_path():
    """Return path to Haar cascade, compatible with Pi"""
    if hasattr(cv2, "data"):
        return os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    return "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

def extract_face_with_rotation(image, margin=0.2, fallback_angles=[-30,30,-15,15]):
    """Detect face and crop, retrying small rotations"""
    haar_path = get_haar_path()
    if not os.path.exists(haar_path):
        print("❌ Haar cascade not found")
        return None

    def try_extract(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(haar_path)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return None
        x, y, w, h = faces[0]
        m_w, m_h = int(w*margin), int(h*(margin+0.5))
        x1, y1 = max(x-m_w,0), max(y-m_h,0)
        x2, y2 = min(x+w+m_w,img.shape[1]), min(y+h+m_h,img.shape[0])
        return img[y1:y2, x1:x2]

    # Try original
    face = try_extract(image)
    if face is not None:
        return face
    # Try rotated
    for angle in fallback_angles:
        face = try_extract(rotate_image(image, angle))
        if face is not None:
            return face
    return None




def send_images_to_api(image_paths):
    """Send images to remote API as multipart/form-data"""
    files = {}
    for i, path in enumerate(image_paths):
        files[f"image_{i}"] = open(path, "rb")
    try:
        response = requests.post(API_URL, files=files, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API returned status {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        for f in files.values():
            f.close()
            
            
            
            
            
            
            
            
 #for simulaing the api sedn receive           
def send_images_to_simulated_api(image_paths):
    """
    Simulated API call: send multiple images at once.
    Returns a fake JSON response after a short delay.
    """
    print("🔹 Simulating sending images to API...")
    for i, path in enumerate(image_paths):
        print(f"  Sending {path} as image_{i}")

    # Simulate network delay / processing time
    time.sleep(2)  # 2 seconds to mimic real API call

    # Simulated response
    simulated_response = {
        "status": "success",
        "processed_images": [os.path.basename(p) for p in image_paths],
        "analysis": [
            {"image": os.path.basename(p), "result": "OK"} for p in image_paths
        ]
    }

    print("🔹 Simulated API response received")
    return simulated_response           
            
            
            
            
            
            
            
            

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
            # FPS overlay
            curr = time.time()
            fps = 1.0/(curr-prev_time) if curr-prev_time>0 else 0
            prev_time = curr
            cv2.putText(frame, f"FPS:{fps:.2f}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255),3,cv2.LINE_AA)
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
    if request.method=="POST":
        # --- Capture burst ---
        frames = []
        interval = CAPTURE_DURATION / CAPTURE_BURST_COUNT
        for _ in range(CAPTURE_BURST_COUNT):
            with frame_lock:
                if latest_frame is not None:
                    frames.append(latest_frame.copy())
            time.sleep(interval)
        
        # Save all captured frames
        captured_paths = [save_frame(f, folder="captured_images") for f in frames]

        # Select TOP_N best frames by sharpness
        frames_sorted = sorted(frames, key=image_quality, reverse=True)[:TOP_N]
        best_paths = []
        for i, f in enumerate(frames_sorted):
            path = save_frame(f, folder="best", prefix=f"best_{i}")
            best_paths.append(path)




        # Send to remote API and get JSON response | or simulate
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

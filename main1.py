#!/usr/bin/env python3
from flask import Flask, Response, render_template_string, request, jsonify
from picamera2 import Picamera2
import cv2
import numpy as np
import threading
import time
import os

app = Flask(__name__)

# ---------------- Camera Setup ----------------
picam2 = Picamera2()

# Configure for 16:9 or 4:3 aspect ratio depending on your calibration
config = picam2.create_video_configuration(
    main={"size": (640, 480), "format": "XRGB8888"},  # good for OpenCV
    buffer_count=2
)
picam2.configure(config)
picam2.start()

# Optional: Control camera exposure / gain / white balance
picam2.set_controls({
    "AwbMode": "auto",
    "Brightness": 0.0,
    "Contrast": 1.0,
    "ExposureTime": 10000,  # microseconds (adjust as needed)
    "AnalogueGain": 1.0
})

# Shared latest frame and a condition variable
latest_frame = None
frame_lock = threading.Condition()

# ---------------- Frame Updater ----------------
def update_camera():
    """ Continuously capture frames from PiCamera2 """
    global latest_frame
    prev_time = time.time()

    while True:
        frame = picam2.capture_array()
        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

            # Calculate FPS
            current_time = time.time()
            elapsed = current_time - prev_time
            prev_time = current_time
            fps = 1.0 / elapsed if elapsed > 0 else 0

            # Draw FPS overlay
            cv2.putText(
                frame,
                f"FPS: {fps:.2f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 0, 255),
                3,
                cv2.LINE_AA
            )

            # Store the frame safely
            with frame_lock:
                latest_frame = frame
                frame_lock.notify_all()

        time.sleep(0.01)  # avoid 100% CPU usage


# ---------------- HTML Template ----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Camera Stream</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #121212; color: #E0E0E0; margin: 0; }
        .top-bar { display: flex; justify-content: space-between; align-items: flex-start; padding: 20px; }
        #video { border: 2px solid #333; width: 400px; height: 300px; background-color: #1E1E1E; }
        button { padding: 10px 20px; font-size: 18px; border-radius: 10px; background-color: #3D5AFE;
                 color: white; border: none; cursor: pointer; margin: 40px; transition: 0.2s; }
        button:hover { background-color: #5C6BC0; }
        .info { padding: 10px 40px; }
        #status { font-weight: bold; color: #00E676; margin-bottom: 8px; }
        #result { background-color: #1E1E1E; padding: 10px; border-radius: 6px; font-family: monospace;
                  white-space: pre-wrap; max-width: 400px; border: 1px solid #333; }
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
            document.getElementById("status").innerText = "Capturing and processing...";
            document.getElementById("result").innerText = "Waiting...";
            fetch("/", { method: "POST" })
                .then(response => response.json())
                .then(data => {
                    document.getElementById("status").innerText = "Done.";
                    document.getElementById("result").innerText = JSON.stringify(data.result, null, 2);
                })
                .catch(err => {
                    document.getElementById("status").innerText = "Error.";
                    console.error(err);
                });
        }
    </script>
</body>
</html>
"""

# ---------------- Helper Functions ----------------
def save_frame(frame, prefix="capture"):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{prefix}_{timestamp}.jpg"
    path = os.path.join(os.getcwd(), filename)
    cv2.imwrite(path, frame)
    print(f"Saved frame to {path}")

def rotate_image(image, angle):
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def extract_face_with_rotation(image, margin=0.2, fallback_angles=[-30, 30, -15, 15]):
    def try_extract(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return None
        x, y, w, h = faces[0]
        m_w = int(w * margin)
        m_h = int(h * (margin + 0.5))
        x1, y1 = max(x - m_w, 0), max(y - m_h, 0)
        x2, y2 = min(x + w + m_w, img.shape[1]), min(y + h + m_h, img.shape[0])
        return img[y1:y2, x1:x2]

    face_crop = try_extract(image)
    if face_crop is not None:
        print("Face found (no rotation).")
        return face_crop

    for angle in fallback_angles:
        rotated = rotate_image(image, angle)
        face_crop = try_extract(rotated)
        if face_crop is not None:
            print(f"Face found after rotating {angle}°.")
            return face_crop

    print("No face found.")
    return None

def image_quality(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

# ---------------- Flask Routes ----------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        frames = []
        for _ in range(4):
            with frame_lock:
                if latest_frame is not None:
                    frames.append(latest_frame.copy())
            time.sleep(0.05)

        if not frames:
            return jsonify({'result': 'Failed to capture frames'}), 500

        best_frame = max(frames, key=image_quality)
        cropped = extract_face_with_rotation(best_frame)
        if cropped is not None:
            save_frame(cropped, "cropped")
        else:
            print("No face found — nothing to save.")

        result = {"name": "Mohammed", "data": ["Has facebook"]}
        return jsonify({'result': result})

    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
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
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ---------------- Run Flask App ----------------
if __name__ == '__main__':
    threading.Thread(target=update_camera, daemon=True).start()
    app.run(host='0.0.0.0', port=5001, threaded=True)

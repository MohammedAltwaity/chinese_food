from flask import Flask, Response, render_template_string, request, jsonify
import cv2
import numpy as np
import threading
import time
import os

app = Flask(__name__)
camera = cv2.VideoCapture(0)

# Shared latest frame and a condition variable
latest_frame = None
frame_lock = threading.Condition()

# Background thread to read camera frames and calculate/display FPS
def update_camera():
    global latest_frame
    prev_time = time.time()

    while True:
        success, frame = camera.read()
        if success:
            frame = cv2.resize(frame, (640, 480))
            # Calculate FPS
            current_time = time.time()
            elapsed = current_time - prev_time
            prev_time = current_time
            fps = 1.0 / elapsed if elapsed > 0 else 0

            # Draw FPS on the frame
            cv2.putText(
                frame,
                f"FPS: {fps:.2f}",
                (10, 30),  # position: top-left
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,       # font scale
                (0, 0, 255),  # color (green)
                4,         # thickness
                cv2.LINE_AA
            )

            # Store the frame with FPS drawn
            with frame_lock:
                latest_frame = frame
                frame_lock.notify_all()
        else:
            print("Failed to read from camera")

        time.sleep(0.01)  # Avoid 100% CPU use



# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Camera Stream</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            font-size: 18px;
            background-color: #121212;
            color: #E0E0E0;
        }

        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 20px;
        }

        #video {
            border: 2px solid #333;
            width: 400px;
            height: 300px;
            background-color: #1E1E1E;
        }

        .top-bar button {
            padding: 10px 20px;
            font-size: 18px;
            border-radius: 10px;
            background-color: #3D5AFE;
            color: white;
            border: none;
            cursor: pointer;
            transition: background-color 0.2s ease;
            margin: 40px;
        }

        .top-bar button:hover {
            background-color: #5C6BC0;
        }

        .info {
            padding: 10px 40px;
        }

        #status {
            font-weight: bold;
            color: #00E676; /* Neon green */
            margin-bottom: 8px;
        }

        #result {
            background-color: #1E1E1E;
            padding: 10px;
            border-radius: 6px;
            font-family: monospace;
            white-space: pre-wrap;
            max-width: 400px;
            color: #E0E0E0;
            border: 1px solid #333;
        }
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




def save_frame(frame, prefix="capture"):
    """
    Saves a frame to the current directory with a timestamped filename.

    Parameters:
    - frame: the image/frame to save (as a NumPy array)
    - prefix: filename prefix (default = "capture")
    """
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
    """
    Tries to extract a face with margin from the original image.
    If no face is found, rotates the image at fallback angles.

    Parameters:
        image: Input image (BGR)
        margin: Margin around detected face
        fallback_angles: Angles to try if original fails

    Returns:
        Cropped face region with margin (or None if not found)
    """
    def try_extract(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return None
        x, y, w, h = faces[0]
        m_w = int(w * margin)
        m_h = int(h * (margin + 0.5))
        x1 = max(x - m_w, 0)
        y1 = max(y - m_h, 0)
        x2 = min(x + w + m_w, img.shape[1])
        y2 = min(y + h + m_h, img.shape[0])
        return img[y1:y2, x1:x2]

    # Try original image first
    face_crop = try_extract(image)
    if face_crop is not None:
        print("Face found (no rotation).")
        return face_crop

    # Try rotated images
    for angle in fallback_angles:
        rotated = rotate_image(image, angle)
        face_crop = try_extract(rotated)
        if face_crop is not None:
            print(f"Face found after rotating {angle}°.")
            return face_crop

    print("No face found in original or rotated images.")
    return None



def extract_face(image, margin=0.2):
    """
    Detects and extracts the first face found in the image, with optional margin.

    Parameters:
        image: Input image (NumPy array in BGR format)
        margin: Margin around the detected face (as a percentage of face size)

    Returns:
        Cropped face region with margin (or None if no face found)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        print("No face detected.")
        return None

    x, y, w, h = faces[0]

    # Calculate margin in pixels
    m_w = int(w * margin)
    m_h = int(h * (margin + 0.5))

    # Expand box and clamp to image bounds
    x1 = max(x - m_w, 0)
    y1 = max(y - m_h, 0)
    x2 = min(x + w + m_w, image.shape[1])
    y2 = min(y + h + m_h, image.shape[0])

    face_crop = image[y1:y2, x1:x2]
    return face_crop







# Stream MJPEG to browser
def generate_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is None:
                frame_lock.wait()
                continue
            frame = latest_frame.copy()
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)  # ~30 FPS







# Capture a number of frames for analysis
def capture_frames(count=4):
    frames = []
    while len(frames) < count:
        with frame_lock:
            if latest_frame is not None:
                frames.append(latest_frame.copy())
        time.sleep(0.01)
    return frames




# Image sharpness estimation
def image_quality(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        frames = capture_frames()
        if not frames:
            return jsonify({'result': 'Failed to capture frames'}), 500

        best_frame = max(frames, key=image_quality)
        
        
        
        

        cropped = extract_face_with_rotation(best_frame)
        if cropped is not None:
            save_frame(cropped, "cropped")
        else:
            print("Face not found — nothing to save.")





    
    
        _, buffer = cv2.imencode('.jpg', best_frame)
        files = {'image': ('best.jpg', buffer.tobytes(), 'image/jpeg')}

        try:
            # Replace with actual external service call if needed
            # response = requests.post("http://your-service/analyze", files=files)
            # result = response.json()
            result = {"name": "Mohammed", "data": ["Has facebook"]}
        except Exception as e:
            result = {"error": str(e)}

        return jsonify({'result': result})

    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Start app and frame updater
if __name__ == '__main__':
    threading.Thread(target=update_camera, daemon=True).start()
    app.run(host='0.0.0.0', port=5001, threaded=True)



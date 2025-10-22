#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Folder to save received images
RECEIVED_FOLDER = "received_images"
os.makedirs(RECEIVED_FOLDER, exist_ok=True)

@app.route('/process_images', methods=['POST'])
def process_images():
    """
    Receive multiple images via multipart/form-data.
    Each image is expected as 'image_0', 'image_1', etc.
    """
    if 'image_0' not in request.files:
        return jsonify({"error": "No images received"}), 400

    received_files = []
    for key in request.files:
        file = request.files[key]
        filename = file.filename
        save_path = os.path.join(RECEIVED_FOLDER, filename)
        file.save(save_path)
        received_files.append(filename)
        print(f"✅ Saved {filename} to {save_path}")

    # Simulate processing on these images
    results = []
    for fname in received_files:
        # Here you would do actual image analysis
        results.append({"image": fname, "result": "OK"})  # Dummy result

    return jsonify({"status": "success", "processed_images": received_files, "analysis": results})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)

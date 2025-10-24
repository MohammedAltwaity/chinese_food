#!/usr/bin/env python3
"""
Image Receiver Server
=====================

Flask API server that receives images from Raspberry Pi via HTTP POST
and saves them to the chinese_food/images/ folder.

Features:
- HTTP POST endpoint for image uploads
- Image validation (format and size)
- Unique filename generation
- JSON confirmation responses
- Comprehensive logging
- Error handling
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_receiver.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
def load_config():
    """Load server configuration from JSON file"""
    try:
        config_path = Path('server_config.json')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning("server_config.json not found, using default configuration")
            return get_default_config()
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return get_default_config()

def get_default_config():
    """Return default configuration"""
    return {
        "host": "0.0.0.0",
        "port": 5000,
        "save_directory": "images",
        "allowed_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "max_file_size_mb": 10,
        "require_api_key": False,
        "api_key": "your-secret-key-here"
    }

# Load configuration
config = load_config()

# Configure Flask
app.config['MAX_CONTENT_LENGTH'] = config['max_file_size_mb'] * 1024 * 1024  # Convert MB to bytes

# Ensure save directory exists
save_dir = Path(config['save_directory'])
save_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"Save directory: {save_dir.absolute()}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in config['allowed_extensions']

def generate_filename(original_filename):
    """Generate unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = secure_filename(original_filename)
    name, ext = os.path.splitext(safe_filename)
    
    # Generate unique filename
    filename = f"rpi_image_{timestamp}_{name}{ext}"
    
    # Ensure uniqueness by adding counter if file exists
    counter = 1
    original_filename = filename
    while (save_dir / filename).exists():
        name, ext = os.path.splitext(original_filename)
        filename = f"{name}_{counter}{ext}"
        counter += 1
    
    return filename

def validate_api_key():
    """Validate API key if required"""
    if not config['require_api_key']:
        return True
    
    # Check for API key in headers or form data
    api_key = request.headers.get('X-API-Key') or request.form.get('api_key')
    return api_key == config['api_key']

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload from Raspberry Pi"""
    try:
        # Get client IP for logging
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        logger.info(f"Image upload request from IP: {client_ip}")
        
        # Validate API key if required
        if not validate_api_key():
            logger.warning(f"Invalid API key from IP: {client_ip}")
            return jsonify({
                "status": "error",
                "message": "Invalid API key"
            }), 401
        
        # Check if image file is present
        if 'image' not in request.files:
            logger.error("No image file in request")
            return jsonify({
                "status": "error",
                "message": "No image file provided"
            }), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            logger.error(f"Invalid file format: {file.filename}")
            return jsonify({
                "status": "error",
                "message": f"Invalid file format. Allowed: {', '.join(config['allowed_extensions'])}"
            }), 400
        
        # Generate unique filename
        filename = generate_filename(file.filename)
        file_path = save_dir / filename
        
        # Save file
        try:
            file.save(str(file_path))
            logger.info(f"Image saved successfully: {filename}")
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            return jsonify({
                "status": "error",
                "message": "Failed to save image"
            }), 500
        
        # Get file info
        file_size = file_path.stat().st_size
        received_at = datetime.now().isoformat()
        
        # Prepare success response
        response_data = {
            "status": "success",
            "filename": filename,
            "received_at": received_at,
            "saved_path": str(file_path),
            "file_size_bytes": file_size,
            "original_filename": file.filename
        }
        
        logger.info(f"Upload successful: {filename} ({file_size} bytes)")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in upload_image: {e}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "save_directory": str(save_dir.absolute()),
        "allowed_extensions": config['allowed_extensions'],
        "max_file_size_mb": config['max_file_size_mb']
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Simple index page"""
    return jsonify({
        "message": "Image Receiver Server",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/upload-image (POST)",
            "health": "/api/health (GET)"
        },
        "timestamp": datetime.now().isoformat()
    }), 200

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    logger.error(f"File too large: {e}")
    return jsonify({
        "status": "error",
        "message": f"File too large. Maximum size: {config['max_file_size_mb']}MB"
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

def main():
    """Main function to run the server"""
    logger.info("=" * 60)
    logger.info("IMAGE RECEIVER SERVER")
    logger.info("=" * 60)
    logger.info(f"Host: {config['host']}")
    logger.info(f"Port: {config['port']}")
    logger.info(f"Save directory: {save_dir.absolute()}")
    logger.info(f"Allowed extensions: {', '.join(config['allowed_extensions'])}")
    logger.info(f"Max file size: {config['max_file_size_mb']}MB")
    logger.info(f"API key required: {config['require_api_key']}")
    logger.info("=" * 60)
    
    try:
        app.run(
            host=config['host'],
            port=config['port'],
            debug=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise

if __name__ == '__main__':
    main()

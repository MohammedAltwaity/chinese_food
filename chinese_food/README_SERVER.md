# Image Receiver Server Setup

## Overview
This Flask API server receives images from Raspberry Pi via HTTP POST and saves them to the `images/` folder.

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements_server.txt
```

### 2. Configuration
Edit `server_config.json` to customize settings:
- `host`: Server host (0.0.0.0 for all interfaces)
- `port`: Server port (default: 5000)
- `save_directory`: Folder to save images (default: "images")
- `allowed_extensions`: Supported image formats
- `max_file_size_mb`: Maximum file size limit
- `require_api_key`: Enable/disable API key authentication
- `api_key`: Secret key for authentication

### 3. Running the Server

**Development Mode:**
```bash
python image_receiver_server.py
```

**Production Mode (with Gunicorn):**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 image_receiver_server:app
```

## API Endpoints

### POST /api/upload-image
Upload an image file from Raspberry Pi.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: `image` field with file data
- Optional: `api_key` field if authentication enabled

**Response (Success):**
```json
{
  "status": "success",
  "filename": "rpi_image_20241024_123456.jpg",
  "received_at": "2024-10-24T12:34:56",
  "saved_path": "images/rpi_image_20241024_123456.jpg",
  "file_size_bytes": 123456,
  "original_filename": "photo.jpg"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Invalid file format"
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-10-24T12:34:56",
  "save_directory": "/path/to/images",
  "allowed_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
  "max_file_size_mb": 10
}
```

### GET /
Server information endpoint.

## Testing

### Test with curl:
```bash
curl -X POST -F "image=@test_image.jpg" http://localhost:5000/api/upload-image
```

### Test with Python:
```python
import requests

files = {'image': open('test_image.jpg', 'rb')}
response = requests.post('http://localhost:5000/api/upload-image', files=files)
print(response.json())
```

## Integration with Raspberry Pi

Update the Raspberry Pi configuration to point to this server:
```json
{
  "server_url": "http://YOUR_COMPUTER_IP:5000/api/upload-image"
}
```

Replace `YOUR_COMPUTER_IP` with your computer's local network IP address.

## Security Features

- File extension validation
- File size limits
- Optional API key authentication
- Secure filename handling
- Comprehensive logging

## Logging

All server activity is logged to:
- Console output (real-time)
- `image_receiver.log` file

Log entries include:
- Image upload requests with client IP
- Successful uploads with file details
- Error conditions and rejections
- Server start/stop events

## Troubleshooting

### Common Issues:

1. **Port already in use:**
   - Change port in `server_config.json`
   - Kill existing process: `netstat -ano | findstr :5000`

2. **Permission denied:**
   - Ensure `images/` folder has write permissions
   - Run as administrator if needed

3. **File not saved:**
   - Check disk space
   - Verify folder permissions
   - Check server logs for errors

4. **Connection refused:**
   - Ensure firewall allows port 5000
   - Check if server is running
   - Verify IP address and port

## Production Deployment

For production use, consider:
- Running as a Windows service
- Using a reverse proxy (nginx)
- Implementing SSL/TLS encryption
- Setting up monitoring and alerts
- Regular log rotation

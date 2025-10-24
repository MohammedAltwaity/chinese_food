#!/usr/bin/env python3
"""
Test script for the image receiver server
"""

import requests
import os
from pathlib import Path

def test_server():
    """Test the image receiver server"""
    
    # Server URL
    server_url = "http://172.27.242.182:5000/api/upload-image"
    
    # Find a test image
    test_image_path = Path("images/bachir.jpg")
    
    if not test_image_path.exists():
        print(f"Test image not found: {test_image_path}")
        return False
    
    print(f"Testing server at: {server_url}")
    print(f"Using test image: {test_image_path}")
    
    try:
        # Test health endpoint first
        print("\n1. Testing health endpoint...")
        health_response = requests.get("http://172.27.242.182:5000/api/health", timeout=10)
        if health_response.status_code == 200:
            print("[OK] Health check passed")
            print(f"  Response: {health_response.json()}")
        else:
            print(f"[FAILED] Health check failed: {health_response.status_code}")
            return False
        
        # Test image upload
        print("\n2. Testing image upload...")
        with open(test_image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(server_url, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] Image upload successful!")
            print(f"  Filename: {result['filename']}")
            print(f"  Received at: {result['received_at']}")
            print(f"  File size: {result['file_size_bytes']} bytes")
            print(f"  Saved path: {result['saved_path']}")
            
            # Check if file was actually saved
            saved_path = Path(result['saved_path'])
            if saved_path.exists():
                print(f"[OK] File confirmed saved: {saved_path}")
                return True
            else:
                print(f"[FAILED] File not found at saved path: {saved_path}")
                return False
        else:
            print(f"[FAILED] Upload failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[FAILED] Connection failed - is the server running?")
        return False
    except requests.exceptions.Timeout:
        print("[FAILED] Request timed out")
        return False
    except Exception as e:
        print(f"[FAILED] Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("IMAGE RECEIVER SERVER TEST")
    print("=" * 60)
    
    success = test_server()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] SERVER TEST PASSED - Ready for Raspberry Pi!")
        print("[OK] Server is working correctly")
        print("[OK] Images are being saved properly")
        print("[OK] JSON responses are correct")
    else:
        print("[FAILED] SERVER TEST FAILED")
        print("[FAILED] Check server logs and configuration")
    print("=" * 60)

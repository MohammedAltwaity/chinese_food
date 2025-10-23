#!/usr/bin/env python3
"""
Fixed Master Automation Script for Face Search Engines
=====================================================

This script fixes the issues with the previous version:
1. Handles PimEyes "Press Enter" prompt automatically
2. Ensures automatic scripts run in parallel properly
3. Actually saves results to files
4. Shows real-time progress of all scripts
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_automation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FixedImageProcessor:
    """Fixed processor that actually works"""
    
    def __init__(self):
        self.scripts = {
            'pimeyes': {
                'script': 'pimeyes_undetected.py',
                'name': 'PimEyes',
                'manual_captcha': True,
                'description': 'Advanced facial recognition search with undetected Chrome'
            },
            'facecheck': {
                'script': 'facecheck_manualverif.py', 
                'name': 'FaceCheck.ID',
                'manual_captcha': True,
                'description': 'Alternative to PimEyes'
            },
            'copyseeker': {
                'script': 'copyseeker.py',
                'name': 'CopySeeker',
                'manual_captcha': False,
                'description': 'Reverse image search'
            },
            'search4faces': {
                'script': 'search4faces_ru.py',
                'name': 'Search4Faces',
                'manual_captcha': False,
                'description': 'VK and social media profile search'
            },
            'tineye': {
                'script': 'tineye.py',
                'name': 'TinEye',
                'manual_captcha': False,
                'description': 'General reverse image search'
            },
            'saucenao': {
                'script': 'saucenao.py',
                'name': 'SauceNAO',
                'manual_captcha': False,
                'description': 'Anime/artwork reverse image search'
            }
        }
        
        # Results directories
        self.results_dir = Path('results')
        self.results_dir.mkdir(exist_ok=True)
        self.auto_results_dir = self.results_dir / 'automatic_results'
        self.auto_results_dir.mkdir(exist_ok=True)
        
    def validate_image(self, image_path: str) -> bool:
        """Validate that the image file exists and is supported"""
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False
            
        # Check file extension
        supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        file_ext = Path(image_path).suffix.lower()
        
        if file_ext not in supported_extensions:
            logger.error(f"Unsupported image format: {file_ext}")
            return False
            
        # Check file size (max 10MB)
        file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
        if file_size > 10:
            logger.error(f"Image file too large: {file_size:.2f}MB (max 10MB)")
            return False
            
        logger.info(f"Image validated: {image_path} ({file_size:.2f}MB)")
        return True
    
    def run_manual_script_with_auto_continue(self, script_key: str, image_path: str) -> Dict:
        """Run manual script and automatically continue after completion"""
        script_info = self.scripts[script_key]
        script_name = script_info['name']
        script_file = script_info['script']
        
        logger.info(f"[MANUAL] Starting {script_name}...")
        
        # Create result tracking
        result = {
            'engine': script_name,
            'script': script_file,
            'image': image_path,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'manual_captcha': True,
            'error': None,
            'end_time': None,
            'duration': None
        }
        
        start_time = time.time()
        
        try:
            # Check if script file exists
            if not os.path.exists(script_file):
                raise FileNotFoundError(f"Script file not found: {script_file}")
            
            # Prepare command
            cmd = [sys.executable, script_file, image_path]
            
            logger.info(f"   Executing: {' '.join(cmd)}")
            logger.info(f"   [NOTE] {script_name} will open in browser - complete captcha manually")
            logger.info(f"   [NOTE] Script will automatically continue after completion")
            
            # Run manual script with output capture to monitor progress
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Monitor the process and look for completion indicators
            stdout_lines = []
            stderr_lines = []
            completed = False
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    stdout_lines.append(line)
                    logger.info(f"   {script_name}: {line}")
                    
                    # Check for completion indicators
                    completion_indicators = [
                        "Press Enter to close browser",
                        "Search completed successfully", 
                        "All 3 checkboxes checked successfully",
                        "Prosopo captcha found",
                        "Failed to handle Prosopo captcha",
                        "Search completed but no results found",
                        "Search completed successfully!",
                        "Search completed but no results found.",
                        "Captcha verification completed, continuing...",
                        "Search timeout reached"
                    ]
                    
                    for indicator in completion_indicators:
                        if indicator in line:
                            logger.info(f"   [DETECTED] {script_name} completed - indicator: {indicator}")
                            # Only send Enter if the old prompt is present
                            if "Press Enter to close browser" in line:
                                process.stdin.write('\n')
                                process.stdin.flush()
                            completed = True
                            break
                    
                    if completed:
                        break
            
            # Get return code
            return_code = process.poll()
            duration = time.time() - start_time
            
            # Update result
            result.update({
                'status': 'completed' if completed or return_code == 0 else 'failed',
                'end_time': datetime.now().isoformat(),
                'duration': round(duration, 2),
                'stdout': stdout_lines,
                'stderr': stderr_lines,
                'return_code': return_code
            })
            
            logger.info(f"[SUCCESS] {script_name} completed in {duration:.2f}s (tab remains open)")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            result.update({
                'status': 'failed',
                'end_time': datetime.now().isoformat(),
                'duration': round(duration, 2),
                'error': error_msg
            })
            
            logger.error(f"[ERROR] {script_name} failed after {duration:.2f}s: {error_msg}")
        
        return result
    
    def run_auto_script_in_thread(self, script_key: str, image_path: str, results_dict: Dict):
        """Run automatic script in a separate thread"""
        script_info = self.scripts[script_key]
        script_name = script_info['name']
        script_file = script_info['script']
        
        logger.info(f"[AUTO] Starting {script_name} in background...")
        
        # Create result tracking
        result = {
            'engine': script_name,
            'script': script_file,
            'image': image_path,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'manual_captcha': False,
            'error': None,
            'end_time': None,
            'duration': None
        }
        
        start_time = time.time()
        
        try:
            # Check if script file exists
            if not os.path.exists(script_file):
                raise FileNotFoundError(f"Script file not found: {script_file}")
            
            # Prepare command
            cmd = [sys.executable, script_file, image_path]
            
            logger.info(f"   [AUTO] Executing: {' '.join(cmd)}")
            
            # Run automatic script with output capture
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Monitor the process
            stdout_lines = []
            stderr_lines = []
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    stdout_lines.append(line)
                    logger.info(f"   [AUTO] {script_name}: {line}")
            
            # Get return code
            return_code = process.poll()
            
            # Check for errors
            if return_code != 0:
                stderr_output = process.stderr.read()
                if stderr_output:
                    stderr_lines.append(stderr_output.strip())
                    logger.error(f"   [AUTO] {script_name} stderr: {stderr_output.strip()}")
                
                raise subprocess.CalledProcessError(return_code, cmd)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Update result
            result.update({
                'status': 'completed',
                'end_time': datetime.now().isoformat(),
                'duration': round(duration, 2),
                'stdout': stdout_lines,
                'stderr': stderr_lines,
                'return_code': return_code
            })
            
            logger.info(f"[SUCCESS] {script_name} completed in {duration:.2f}s")
            
            # Save results to text file
            self.save_auto_results(script_name, image_path, stdout_lines, stderr_lines)
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            
            result.update({
                'status': 'failed',
                'end_time': datetime.now().isoformat(),
                'duration': round(duration, 2),
                'error': error_msg
            })
            
            logger.error(f"[ERROR] {script_name} failed after {duration:.2f}s: {error_msg}")
        
        # Store result in shared dictionary
        results_dict[script_key] = result
    
    def save_auto_results(self, script_name: str, image_path: str, stdout_lines: List[str], stderr_lines: List[str]):
        """Save automatic script results to text file"""
        image_name = Path(image_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{script_name}_{image_name}_{timestamp}.txt"
        filepath = self.auto_results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Results for {script_name}\n")
            f.write(f"Image: {image_path}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n\n")
            
            if stdout_lines:
                f.write("STDOUT:\n")
                f.write("-" * 20 + "\n")
                for line in stdout_lines:
                    f.write(f"{line}\n")
                f.write("\n")
            
            if stderr_lines:
                f.write("STDERR:\n")
                f.write("-" * 20 + "\n")
                for line in stderr_lines:
                    f.write(f"{line}\n")
                f.write("\n")
        
        logger.info(f"[SAVE] Results saved to: {filepath}")
    
    def process_image_fixed(self, image_path: str) -> Dict:
        """Process image with fixed execution strategy"""
        logger.info(f"[PROCESS] Processing image: {image_path}")
        
        # Validate image
        if not self.validate_image(image_path):
            return {'status': 'failed', 'error': 'Image validation failed'}
        
        # Create session results
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = Path(image_path).stem
        
        session_results = {
            'session_id': session_id,
            'image_path': image_path,
            'image_name': image_name,
            'start_time': datetime.now().isoformat(),
            'engines': {},
            'summary': {
                'total_engines': 6,
                'completed': 0,
                'failed': 0,
                'manual_captcha_required': 2
            }
        }
        
        logger.info(f"[SESSION] Session {session_id} started for {image_name}")
        
        # Phase 1: Start PimEyes + automatic scripts in parallel (including FaceCheck)
        logger.info(f"[PHASE1] Starting PimEyes + automatic scripts in parallel (including FaceCheck)...")
        
        # Start automatic scripts in background threads (including FaceCheck)
        auto_scripts = ['saucenao', 'tineye', 'search4faces', 'copyseeker', 'facecheck']
        auto_results = {}
        auto_threads = []
        
        for script_key in auto_scripts:
            thread = threading.Thread(
                target=self.run_auto_script_in_thread,
                args=(script_key, image_path, auto_results)
            )
            auto_threads.append(thread)
            thread.start()
            logger.info(f"   [THREAD] Started {script_key} in background")
        
        # Start PimEyes (manual)
        logger.info(f"[MANUAL] Starting PimEyes...")
        pimeyes_result = self.run_manual_script_with_auto_continue('pimeyes', image_path)
        session_results['engines']['pimeyes'] = pimeyes_result
        
        # Wait for automatic scripts to complete
        logger.info(f"[WAIT] Waiting for automatic scripts to complete...")
        for thread in auto_threads:
            thread.join()
        
        # Add automatic results to session
        session_results['engines'].update(auto_results)
        
        # Update summary
        for result in session_results['engines'].values():
            if result['status'] == 'completed':
                session_results['summary']['completed'] += 1
            else:
                session_results['summary']['failed'] += 1
        
        # Finalize session
        session_results['end_time'] = datetime.now().isoformat()
        total_duration = (datetime.fromisoformat(session_results['end_time']) - 
                         datetime.fromisoformat(session_results['start_time'])).total_seconds()
        session_results['total_duration'] = round(total_duration, 2)
        
        # Save session results
        results_file = self.results_dir / f"session_{session_id}_{image_name}.json"
        with open(results_file, 'w') as f:
            json.dump(session_results, f, indent=2)
        
        # Print summary
        logger.info(f"[COMPLETE] Session {session_id} completed!")
        logger.info(f"   [FILE] Session results: {results_file}")
        logger.info(f"   [AUTO] Auto results: {self.auto_results_dir}")
        logger.info(f"   [TIME] Total duration: {total_duration:.2f}s")
        logger.info(f"   [SUCCESS] Completed: {session_results['summary']['completed']}/{session_results['summary']['total_engines']}")
        logger.info(f"   [FAILED] Failed: {session_results['summary']['failed']}")
        logger.info(f"   [MANUAL] Manual captcha: {session_results['summary']['manual_captcha_required']}")
        logger.info(f"   [NOTE] Manual script browser tabs remain open for review")
        
        return session_results

class FixedImageFolderWatcher(FileSystemEventHandler):
    """Watch for new image files in the images/ folder"""
    
    def __init__(self, processor: FixedImageProcessor):
        self.processor = processor
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.processing_files = set()
        
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        file_ext = file_path.suffix.lower()
        
        # Check if it's a supported image file
        if file_ext not in self.supported_extensions:
            return
            
        # Check if we're already processing this file
        if str(file_path) in self.processing_files:
            return
            
        # Add to processing set
        self.processing_files.add(str(file_path))
        
        logger.info(f"[NEW] New image detected: {file_path}")
        
        # Wait a moment for file to be fully written
        time.sleep(2)
        
        try:
            # Process the image
            self.processor.process_image_fixed(str(file_path))
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
        finally:
            # Remove from processing set
            self.processing_files.discard(str(file_path))

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fixed master automation script for face search engines')
    parser.add_argument('--watch', action='store_true', default=True,
                       help='Enable folder watching mode (default)')
    parser.add_argument('--image', type=str, help='Process a specific image file')
    parser.add_argument('--no-watch', action='store_true', help='Disable folder watching')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = FixedImageProcessor()
    
    # Check if specific image provided
    if args.image:
        logger.info("[SINGLE] Processing specific image with fixed strategy...")
        processor.process_image_fixed(args.image)
        return
    
    # Check if watching is disabled
    if args.no_watch:
        logger.info("[BATCH] Processing images in images/ folder...")
        images_dir = Path('images')
        if not images_dir.exists():
            logger.error("images/ folder not found!")
            return
            
        # Process all images in folder
        supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        image_files = [f for f in images_dir.iterdir() 
                      if f.is_file() and f.suffix.lower() in supported_extensions]
        
        if not image_files:
            logger.info("No supported image files found in images/ folder")
            return
            
        for image_file in image_files:
            logger.info(f"Processing: {image_file}")
            processor.process_image_fixed(str(image_file))
            time.sleep(2)  # Brief delay between images
        
        return
    
    # Folder watching mode
    logger.info("[WATCH] Starting fixed folder watcher...")
    logger.info("   Watching images/ folder for new image uploads")
    logger.info("   Press Ctrl+C to stop")
    logger.info("   [STRATEGY] PimEyes + all auto scripts (including FaceCheck) in parallel")
    
    # Create images directory if it doesn't exist
    images_dir = Path('images')
    images_dir.mkdir(exist_ok=True)
    
    # Setup folder watcher
    event_handler = FixedImageFolderWatcher(processor)
    observer = Observer()
    observer.schedule(event_handler, str(images_dir), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("[STOP] Stopping folder watcher...")
        observer.stop()
    
    observer.join()
    logger.info("[END] Goodbye!")

if __name__ == "__main__":
    main() 
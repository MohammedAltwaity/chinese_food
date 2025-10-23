#!/usr/bin/env python3
"""
Auto Image Processor - Folder Watcher
====================================

This script monitors the images/ folder for new image files and automatically
triggers the master_automation_fixed.py script with the latest image.

Features:
- Real-time folder monitoring
- Automatic image processing
- Duplicate detection prevention
- Processing status tracking
- Error handling and recovery
"""

import os
import sys
import time
import json
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_image_processor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutoImageProcessor:
    """Main class for automatic image processing"""
    
    def __init__(self):
        self.images_dir = Path('images')
        self.results_dir = Path('results')
        self.processing_log = Path('processing_log.json')
        
        # Supported image extensions
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Track processed files to avoid duplicates
        self.processed_files: Set[str] = set()
        self.currently_processing: Set[str] = set()
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'duplicates_skipped': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Load previous processing log
        self.load_processing_log()
        
        # Ensure directories exist
        self.images_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("Auto Image Processor initialized")
        logger.info(f"Monitoring directory: {self.images_dir.absolute()}")
        logger.info(f"Supported formats: {', '.join(self.supported_extensions)}")
    
    def load_processing_log(self):
        """Load previous processing log to avoid reprocessing files"""
        try:
            if self.processing_log.exists():
                with open(self.processing_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                    self.stats.update(data.get('stats', {}))
                    logger.info(f"Loaded {len(self.processed_files)} previously processed files")
            else:
                logger.info("No previous processing log found - starting fresh")
        except Exception as e:
            logger.error(f"Error loading processing log: {e}")
            self.processed_files = set()
    
    def save_processing_log(self):
        """Save current processing log"""
        try:
            data = {
                'processed_files': list(self.processed_files),
                'stats': self.stats,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.processing_log, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processing log: {e}")
    
    def is_supported_image(self, file_path: Path) -> bool:
        """Check if file is a supported image format"""
        return file_path.suffix.lower() in self.supported_extensions
    
    def is_file_ready(self, file_path: Path) -> bool:
        """Check if file is fully written and ready for processing"""
        try:
            # Check if file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # Check file size (must be > 0)
            if file_path.stat().st_size == 0:
                return False
            
            # Check if file is still being written (Windows file locking)
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)  # Try to read first byte
                return True
            except (PermissionError, OSError):
                return False
                
        except Exception as e:
            logger.debug(f"Error checking file readiness: {e}")
            return False
    
    def wait_for_file_ready(self, file_path: Path, max_wait: int = 30) -> bool:
        """Wait for file to be fully written"""
        logger.info(f"Waiting for file to be ready: {file_path.name}")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.is_file_ready(file_path):
                logger.info(f"File ready: {file_path.name}")
                return True
            time.sleep(1)
        
        logger.warning(f"File not ready after {max_wait}s: {file_path.name}")
        return False
    
    def process_image(self, image_path: Path) -> bool:
        """Process a single image using the master script"""
        try:
            logger.info(f"[PROCESS] Starting processing: {image_path.name}")
            
            # Add to currently processing set
            self.currently_processing.add(str(image_path))
            
            # Prepare command
            cmd = [sys.executable, 'master_automation_fixed.py', '--image', str(image_path)]
            
            logger.info(f"[CMD] Executing: {' '.join(cmd)}")
            
            # Run master script
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                encoding='utf-8',
                errors='replace'
            )
            
            duration = time.time() - start_time
            
            # Check result
            if result.returncode == 0:
                logger.info(f"[SUCCESS] {image_path.name} processed successfully in {duration:.2f}s")
                self.stats['successful'] += 1
                success = True
            else:
                logger.error(f"[ERROR] {image_path.name} processing failed (code: {result.returncode})")
                logger.error(f"[STDERR] {result.stderr}")
                self.stats['failed'] += 1
                success = False
            
            # Log output for debugging
            if result.stdout:
                logger.info(f"[STDOUT] {image_path.name}: {result.stdout[:500]}...")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error(f"[TIMEOUT] {image_path.name} processing timed out after 30 minutes")
            self.stats['failed'] += 1
            return False
            
        except Exception as e:
            logger.error(f"[EXCEPTION] Error processing {image_path.name}: {e}")
            self.stats['failed'] += 1
            return False
            
        finally:
            # Remove from currently processing set
            self.currently_processing.discard(str(image_path))
            
            # Add to processed files
            self.processed_files.add(str(image_path))
            self.stats['total_processed'] += 1
            
            # Save processing log
            self.save_processing_log()
    
    def process_image_async(self, image_path: Path):
        """Process image in a separate thread"""
        def process_thread():
            try:
                self.process_image(image_path)
            except Exception as e:
                logger.error(f"Error in processing thread for {image_path.name}: {e}")
        
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
        logger.info(f"[THREAD] Started processing thread for: {image_path.name}")
    
    def print_stats(self):
        """Print current processing statistics"""
        logger.info("=" * 60)
        logger.info("PROCESSING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        logger.info(f"Currently processing: {len(self.currently_processing)}")
        logger.info(f"Start time: {self.stats['start_time']}")
        logger.info("=" * 60)

class ImageFolderWatcher(FileSystemEventHandler):
    """Watchdog event handler for image folder monitoring"""
    
    def __init__(self, processor: AutoImageProcessor):
        self.processor = processor
        self.last_processed = {}  # Track last modification time per file
    
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if it's a supported image
        if not self.processor.is_supported_image(file_path):
            return
        
        # Check if already processed
        if str(file_path) in self.processor.processed_files:
            logger.info(f"[SKIP] Already processed: {file_path.name}")
            self.processor.stats['duplicates_skipped'] += 1
            return
        
        # Check if currently processing
        if str(file_path) in self.processor.currently_processing:
            logger.info(f"[SKIP] Currently processing: {file_path.name}")
            return
        
        logger.info(f"[NEW] New image detected: {file_path.name}")
        
        # Wait for file to be ready
        if not self.processor.wait_for_file_ready(file_path):
            logger.error(f"[ERROR] File not ready: {file_path.name}")
            return
        
        # Process the image
        self.processor.process_image_async(file_path)
    
    def on_modified(self, event):
        """Handle file modification (for files being written)"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process if it's a supported image and not already processed
        if (self.processor.is_supported_image(file_path) and 
            str(file_path) not in self.processor.processed_files and
            str(file_path) not in self.processor.currently_processing):
            
            # Check if file is ready now
            if self.processor.is_file_ready(file_path):
                logger.info(f"[READY] File ready after modification: {file_path.name}")
                self.processor.process_image_async(file_path)

def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("AUTO IMAGE PROCESSOR - FOLDER WATCHER")
    logger.info("=" * 60)
    logger.info("Monitoring images/ folder for new image files")
    logger.info("Automatically triggers master_automation_fixed.py")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # Initialize processor
    processor = AutoImageProcessor()
    
    # Print initial stats
    processor.print_stats()
    
    # Setup folder watcher
    event_handler = ImageFolderWatcher(processor)
    observer = Observer()
    observer.schedule(event_handler, str(processor.images_dir), recursive=False)
    
    try:
        # Start watching
        observer.start()
        logger.info(f"[WATCH] Started monitoring: {processor.images_dir.absolute()}")
        
        # Main loop
        while True:
            time.sleep(10)  # Check every 10 seconds
            
            # Print stats every 5 minutes
            if int(time.time()) % 300 == 0:
                processor.print_stats()
                
    except KeyboardInterrupt:
        logger.info("[STOP] Stopping folder watcher...")
        observer.stop()
    
    observer.join()
    
    # Final stats
    processor.print_stats()
    logger.info("[END] Auto Image Processor stopped")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Batch Image Processor
====================

Process all existing images in the images/ folder using the master script.
This is useful for processing images that were added before the auto processor was running.
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def process_existing_images():
    """Process all existing images in the images/ folder"""
    
    images_dir = Path('images')
    if not images_dir.exists():
        logger.error("images/ folder not found!")
        return
    
    # Supported image extensions
    supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    # Find all image files
    image_files = []
    for file_path in images_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            image_files.append(file_path)
    
    if not image_files:
        logger.info("No image files found in images/ folder")
        return
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    # Process each image
    successful = 0
    failed = 0
    
    for i, image_path in enumerate(image_files, 1):
        logger.info(f"[{i}/{len(image_files)}] Processing: {image_path.name}")
        
        try:
            # Prepare command
            cmd = [sys.executable, 'master_automation_fixed.py', '--image', str(image_path)]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
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
                logger.info(f"✓ {image_path.name} processed successfully in {duration:.2f}s")
                successful += 1
            else:
                logger.error(f"✗ {image_path.name} processing failed (code: {result.returncode})")
                if result.stderr:
                    logger.error(f"Error: {result.stderr}")
                failed += 1
            
            # Brief delay between images
            if i < len(image_files):
                time.sleep(2)
                
        except subprocess.TimeoutExpired:
            logger.error(f"✗ {image_path.name} processing timed out after 30 minutes")
            failed += 1
            
        except Exception as e:
            logger.error(f"✗ Error processing {image_path.name}: {e}")
            failed += 1
    
    # Final summary
    logger.info("=" * 60)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total images: {len(image_files)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {(successful/len(image_files)*100):.1f}%")
    logger.info("=" * 60)

def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("BATCH IMAGE PROCESSOR")
    logger.info("=" * 60)
    logger.info("Processing all existing images in images/ folder")
    logger.info("=" * 60)
    
    process_existing_images()

if __name__ == "__main__":
    main()

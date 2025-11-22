"""File download utilities for Flutter Project Launcher Tool."""
import os
import requests
from pathlib import Path
from typing import Optional, Callable
from core.logger import Logger


class Downloader:
    """File downloader with progress tracking."""
    
    def __init__(self):
        self.logger = Logger()
    
    def download_file(self, url: str, destination: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """
        Download a file with progress tracking.
        
        Args:
            url: URL to download from
            destination: Local file path to save to
            progress_callback: Callback function(bytes_downloaded, total_bytes)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            destination_path = Path(destination)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Stream download to show progress
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)
            
            self.logger.info(f"Downloaded {destination} ({downloaded} bytes)")
            return True
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            # Clean up partial download
            if os.path.exists(destination):
                try:
                    os.remove(destination)
                except:
                    pass
            return False


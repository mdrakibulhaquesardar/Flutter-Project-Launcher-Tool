"""Thread for installing Flutter SDK from ZIP file."""
import zipfile
import shutil
import os
import time
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal
from core.logger import Logger


class SDKInstallThread(QThread):
    """Thread for installing Flutter SDK from ZIP."""
    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(bool, str)  # success, message_or_path
    
    def __init__(self, zip_path: str, version: str, install_dir: Path):
        super().__init__()
        self.zip_path = zip_path
        self.version = version
        self.install_dir = install_dir
        self.logger = Logger()
    
    def run(self):
        """Install SDK from ZIP file."""
        try:
            zip_path_obj = Path(self.zip_path)
            
            if not zip_path_obj.exists():
                self.finished.emit(False, f"ZIP file not found: {self.zip_path}")
                return
            
            # Remove existing installation if any
            if self.install_dir.exists():
                self.progress.emit("Removing existing installation...")
                shutil.rmtree(self.install_dir)
            
            # Extract ZIP with progress
            self.progress.emit(f"Extracting Flutter SDK {self.version}...")
            self.logger.info(f"Extracting Flutter SDK from {self.zip_path} to {self.install_dir.parent}")
            
            # Get total file count for progress
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                extracted = 0
                
                # Extract files one by one to show progress
                for file_info in zip_ref.infolist():
                    zip_ref.extract(file_info, self.install_dir.parent)
                    extracted += 1
                    
                    # Update progress every 100 files or at milestones
                    if extracted % 100 == 0 or extracted == total_files:
                        percent = int((extracted / total_files) * 100)
                        self.progress.emit(f"Extracting... {percent}% ({extracted}/{total_files} files)")
            
            # Flutter SDK is extracted to a 'flutter' folder, rename it
            extracted_flutter = self.install_dir.parent / "flutter"
            if extracted_flutter.exists():
                self.progress.emit("Finalizing installation...")
                extracted_flutter.rename(self.install_dir)
            else:
                # Sometimes SDK might be extracted directly
                self.logger.warning(f"Flutter folder not found at {extracted_flutter}, checking {self.install_dir.parent}")
            
            # Verify installation
            self.progress.emit("Verifying installation...")
            flutter_bin = self.install_dir / "bin" / ("flutter.bat" if os.name == 'nt' else "flutter")
            if not flutter_bin.exists():
                self.finished.emit(False, "SDK installation verification failed: flutter executable not found")
                return
            
            # Close ZIP file handle explicitly before deletion
            self.progress.emit("Cleaning up...")
            
            # Delete ZIP file with retry logic
            zip_deleted = False
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # Ensure file handle is closed
                    if zip_path_obj.exists():
                        os.remove(self.zip_path)
                        zip_deleted = True
                        self.logger.info(f"Deleted ZIP file: {self.zip_path}")
                        break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        time.sleep(0.5)  # Wait 500ms before retry
                        self.logger.warning(f"Retry {attempt + 1}/{max_retries} deleting ZIP file")
                    else:
                        self.logger.warning(f"Could not delete ZIP file after {max_retries} attempts: {e}")
                except Exception as e:
                    self.logger.warning(f"Error deleting ZIP file: {e}")
                    break
            
            if not zip_deleted:
                self.logger.warning(f"ZIP file not deleted: {self.zip_path} (may be in use)")
            
            sdk_path = str(self.install_dir)
            
            # Add to settings
            from services.flutter_service import FlutterService
            flutter_service = FlutterService()
            flutter_service.settings.add_flutter_sdk(sdk_path)
            
            self.progress.emit("Installation completed!")
            self.logger.info(f"Flutter SDK {self.version} installed at {sdk_path}")
            self.finished.emit(True, sdk_path)
            
        except zipfile.BadZipFile:
            self.finished.emit(False, "Invalid ZIP file. Download may be corrupted.")
        except Exception as e:
            self.logger.error(f"Error installing SDK: {e}")
            self.finished.emit(False, str(e))


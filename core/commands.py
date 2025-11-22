"""Command execution utilities for Flutter Project Launcher Tool."""
import subprocess
import os
from typing import Optional, List
from PyQt6.QtCore import QThread, pyqtSignal


class FlutterCommandThread(QThread):
    """Async execution of Flutter commands."""
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(int)  # exit code
    
    def __init__(self, command: List[str], cwd: Optional[str] = None, env: Optional[dict] = None):
        super().__init__()
        self.command = command
        self.cwd = cwd
        self.env = env or os.environ.copy()
        self.process = None
    
    def run(self):
        """Execute the command and emit output signals."""
        try:
            import os
            import time
            import sys
            
            # On Windows, for .bat files, we might need special handling
            # Set environment to disable Python buffering for better real-time output
            env = self.env.copy()
            if os.name == 'nt':  # Windows
                env['PYTHONUNBUFFERED'] = '1'
            
            # For Windows .bat files, we need to ensure output is properly captured
            # Don't use CREATE_NO_WINDOW as it might prevent output capture
            
            # Merge stderr with stdout for simpler reading
            # Use line buffering for real-time output (bufsize=1 works better than 0 on Windows)
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                cwd=self.cwd,
                env=env,
                text=True,
                bufsize=1,  # Line buffered (works better on Windows)
                universal_newlines=True,
                shell=False  # Don't use shell for better output capture
            )
            
            # Read output line by line using iter
            # This is the most reliable way to get real-time output
            output_received = False
            
            # Use a more robust reading method
            while True:
                # Check if process has finished
                if self.process.poll() is not None:
                    # Process finished, read any remaining output
                    try:
                        remaining = self.process.stdout.read()
                        if remaining:
                            for rem_line in remaining.splitlines():
                                rem_line = rem_line.strip()
                                if rem_line:
                                    self.output.emit(rem_line)
                                    output_received = True
                    except Exception:
                        pass
                    break
                
                # Try to read a line
                line = self.process.stdout.readline()
                if line:
                    output_received = True
                    # Strip trailing newlines but preserve content
                    clean_line = line.rstrip('\n\r')
                    if clean_line:  # Only emit non-empty lines
                        self.output.emit(clean_line)
                else:
                    # No output yet, small sleep to avoid busy waiting
                    time.sleep(0.01)
            
            # Wait for process to complete and get exit code
            exit_code = self.process.wait()
            
            # Read any remaining output that might be buffered
            try:
                # Try to read any remaining data
                import select
                if hasattr(select, 'select'):
                    # Unix-like system
                    if select.select([self.process.stdout], [], [], 0)[0]:
                        remaining = self.process.stdout.read()
                        if remaining:
                            for line in remaining.splitlines():
                                if line.strip():
                                    self.output.emit(line.strip())
                else:
                    # Windows - try to read remaining
                    remaining = self.process.stdout.read()
                    if remaining:
                        for line in remaining.splitlines():
                            if line.strip():
                                self.output.emit(line.strip())
            except Exception:
                # If reading remaining fails, that's okay
                pass
            
            # If no output was received and exit code is not 0, try to get error info
            if not output_received and exit_code != 0:
                self.output.emit(f"Command failed with exit code {exit_code}")
                self.output.emit("No output was captured. This might indicate a problem with the command execution.")
            
            self.finished.emit(exit_code)
            
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            self.error.emit(error_msg)
            self.output.emit(error_msg)
            import traceback
            tb = traceback.format_exc()
            self.output.emit(tb)
            self.finished.emit(1)
    
    def stop(self):
        """Terminate the running process."""
        if self.process:
            self.process.terminate()


class CommandExecutor:
    """Synchronous command executor for quick operations."""
    
    @staticmethod
    def run_command(command: List[str], cwd: Optional[str] = None, 
                   env: Optional[dict] = None) -> tuple[str, int]:
        """
        Run command synchronously and return output and exit code.
        
        Returns:
            tuple: (output, exit_code)
        """
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env or os.environ.copy(),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout + result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "Command timed out", 1
        except Exception as e:
            return str(e), 1



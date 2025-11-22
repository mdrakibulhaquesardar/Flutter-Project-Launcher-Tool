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
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.cwd,
                env=self.env,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output.emit(line.strip())
            
            self.process.wait()
            self.finished.emit(self.process.returncode)
            
        except Exception as e:
            self.error.emit(str(e))
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



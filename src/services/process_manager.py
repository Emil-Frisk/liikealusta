import subprocess
import os
import sys
import signal
from pathlib import Path
from utils.utils import get_exe_temp_dir,find_venv_python
import time
import psutil

class ProcessManager:
    def __init__(self, logger, target_dir):
        self.processes = {}
        self.logger = logger
        self.entry_point = self.get_entry_point()
        self.target_dir = target_dir

    def launch_module(self, file_name, args=None):
        """Launch a Python file_name and return PID or none if error"""
        try:
            ### Support filenames with .py and w/o it
            res = file_name.split(".py")
            if len(res) == 2:
                file_name = res[0]
            
            if getattr(sys, 'frozen', False):
                # PyInstaller context - use the executable path
                base_dir = os.path.dirname(sys.executable)
                temp_exe_dir = get_exe_temp_dir()
                cmd =  ["C:\liikealusta\.venv\Scripts\python.exe", temp_exe_dir]
            else:
                file_path = os.path.join(self.target_dir, f"{file_name}.py")
                venv_python = find_venv_python()
                
                ### adding file_name to the launch options to find and check for its existance later
                cmd =  [venv_python, file_path, f"entrypoint={file_name}"]
                
            ### Prevent process recursion
            if self.entry_point == file_name:
                self.logger.error("Recursion spotted not spawning a new process")
                return 
            
            if args:
                cmd.extend(args)
                
            process = subprocess.Popen(
                cmd
            )

            pid = process.pid
            self.processes[pid] = {
                'process': process,
                'file_name': file_name,
                'launch-time': time.time()
            }
            self.logger.info(f"Launched {file_name} with PID: {process.pid}")
            return pid
            
        except Exception as e:
            self.logger.error(f"Failed to launch process {file_name}: {e}")
            return None

    def cleanup_module(self, pid):
        """Cleanup a specific file_name by PID"""
        if pid not in self.processes:
            self.logger.error(f"No process found with PID: {pid}")
            return False
            
        process_info = self.processes[pid]
        process = process_info['process']
        
        try:
            # Check if the process is still running and is a Python process
            ps_process = psutil.Process(pid)
            process_name = ps_process.name().lower()

            self.logger.info((f"process_name {process_name}"))

            if 'python' not in process_name and not process_name.endswith('.exe'):
                self.logger.error(f"Process with PID {pid} is not a Python process: {process_name}")
                del self.processes[pid]
                return False

            # First try graceful termination
            process.kill()
            self.logger.warning(f"Force killed process {process_info['file_name']} with PID {process.pid}")

        except Exception as e:
            self.logger.error(f"Error during process cleanup: {e}")
            return False
            
        finally:
            # Cleanup regardless of success
            del self.processes[pid]
            self.logger.info(f"Cleaned up process with PID {pid}")
            return True

    def cleanup_all(self):
        """Cleanup all running processes"""
        for pid in list(self.processes.keys()):
            self.cleanup_module(pid)

    def get_entry_point(self):
        return Path(sys.argv[0]).name.split(".py")[0]



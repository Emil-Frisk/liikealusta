import subprocess
import os
import sys
import signal
from pathlib import Path
from utils.utils import get_exe_temp_dir,find_venv_python
import time
import psutil

class ModuleManager:
    def __init__(self, logger):
        self.processes = {}
        self.logger = logger
        self.entry_point = self.get_entry_point()

    def launch_module(self, module_path, args=None):
        """Launch a Python module and return PID or none if error"""
        try:
            if args:
                cmd.extend(args)

            if getattr(sys, 'frozen', False):
                # PyInstaller context - use the executable path
                base_dir = os.path.dirname(sys.executable)
                temp_exe_dir = get_exe_temp_dir()
                cmd =  ["C:\liikealusta\.venv\Scripts\python.exe", temp_exe_dir]
            else:
                # Normal context - use the script path  
                src_dir = Path(__file__).parent.parent
                file_path = os.path.join(src_dir, f"{module_path}.py")
                venv_python = find_venv_python()
                
                ### adding module to the launch options to find and check for its existance later
                cmd =  [venv_python, file_path, f"entrypoint={module_path}"]

            ### Prevent process recursion
            if self.entry_point == module_path:
                self.logger.error("Recursion spotted not spawning a new process")
                return 
            
            process = subprocess.Popen(
                cmd
            )

            pid = process.pid
            self.processes[pid] = {
                'process': process,
                'module': module_path,
                'launch-time': time.time()
            }
            self.logger.info(f"Launched {module_path} with PID: {process.pid}")
            return pid
            
        except Exception as e:
            self.logger.error(f"Failed to launch process {module_path}: {e}")
            return None

    def cleanup_module(self, pid):
        """Cleanup a specific module by PID"""
        if pid not in self.processes:
            self.logger.error(f"No process found with PID: {pid}")
            return False
            
        process_info = self.processes[pid]
        process = process_info['process']
        
        try:
            # Check if the process is still running and is a Python process
            ps_process = psutil.Process(pid)
            process_name = ps_process.name().lower()

            print(f"process_name {process_name}")

            if 'python' not in process_name and not process_name.endswith('.exe'):
                self.logger.error(f"Process with PID {pid} is not a Python process: {process_name}")
                del self.processes[pid]
                return False

            # First try graceful termination
            process.kill()
            self.logger.warning(f"Force killed process {process_info['module']} with PID {process.pid}")

        except Exception as e:
            self.logger.error(f"Error during module cleanup: {e}")
            return False
            
        finally:
            # Cleanup regardless of success
            del self.processes[pid]
            self.logger.error(f"Cleaned up module with PID {pid}")
            return True

    def cleanup_all(self):
        """Cleanup all running modules"""
        for pid in list(self.processes.keys()):
            self.cleanup_module(pid)

    def get_entry_point(self):
        return Path(sys.argv[0]).name.split(".py")[0]


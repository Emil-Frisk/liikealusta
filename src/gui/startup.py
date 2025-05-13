import sys
import json
import os
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox, QTabWidget, QFormLayout
from PyQt6.QtGui import QFont
import requests
import runpy
from utils.setup_logging import setup_logging

CONFIG_FILE = "config.json"

class ServerStartupGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = setup_logging("startup", "startup.log")
        self.project_root = ""
        
        self.setWindowTitle("Server Startup")
        self.setGeometry(100, 100, 400, 350)
        
        # Set font
        font = QFont("Arial", 14)
        self.setFont(font)
        
        self.main_layout = QVBoxLayout()

        # Create Tab Widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # General Tab
        self.general_tab = QWidget()
        self.general_layout = QFormLayout()

        # Speed Field
        self.speed_input = QSpinBox()
        self.speed_input.setRange(1, 500)
        self.general_layout.addRow("Velocity (RPM):", self.speed_input)

        # Acceleration Field
        self.accel_input = QSpinBox()
        self.accel_input.setRange(1, 1000)
        self.general_layout.addRow("Acceleration (RPM):", self.accel_input)

        # Add general layout to general tab
        self.general_tab.setLayout(self.general_layout)
        self.tabs.addTab(self.general_tab, "General")

        # Advanced Tab
        self.advanced_tab = QWidget()
        self.advanced_layout = QFormLayout()

        # Update Frequency Field (1-70 Hz)
        self.freq_input = QSpinBox()
        self.freq_input.setRange(1, 70)
        self.advanced_layout.addRow("Update Frequency (Hz):", self.freq_input)

        # IP Field for Servo Arm 1
        self.ip_input1 = QLineEdit()
        self.advanced_layout.addRow("Servo Arm 1 IP:", self.ip_input1)

        # IP Field for Servo Arm 2
        self.ip_input2 = QLineEdit()
        self.advanced_layout.addRow("Servo Arm Servo 2 IP:", self.ip_input2)

        # Add advanced layout to advanced tab
        self.advanced_tab.setLayout(self.advanced_layout)
        self.tabs.addTab(self.advanced_tab, "Advanced")

        # Load last used values
        self.load_config()

        # Start Button
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.start_server)
        self.main_layout.addWidget(self.start_button)
        
        # Shutdown Button (Initially Disabled)
        self.shutdown_button = QPushButton("Shutdown Server")
        self.shutdown_button.setEnabled(False)
        self.shutdown_button.clicked.connect(self.shutdown_server)
        self.main_layout.addWidget(self.shutdown_button)

        self.set_styles()
        
        self.setLayout(self.main_layout)

    def set_styles(self):
        styles_path = os.path.join(Path(__file__).parent, "styles.json")
        # Load the JSON from the file
        try:
            with open(styles_path, "r") as f:
                data = json.load(f)

            # Apply the styles to your buttons
            for style in data["styles"]:
                if "start_up_btn" in style:
                    self.start_button.setStyleSheet(style["start_up_btn"])
                if "shutdown_btn" in style:
                    self.shutdown_button.setStyleSheet(style["shutdown_btn"])
        except FileNotFoundError:
            print(f"Error: styles.json not found at {styles_path}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    def load_config(self):
        try:
            root = Path(__file__).parent
            config_path = os.path.join(root, CONFIG_FILE)
            with open(config_path, "r") as f:
                config = json.load(f)
                self.ip_input1.setText(config.get("servo_ip_1", ""))
                self.ip_input2.setText(config.get("servo_ip_2", ""))
                self.freq_input.setValue(config.get("update_frequency", 10))
                self.speed_input.setValue(config.get("speed", 50))
                self.accel_input.setValue(config.get("acceleration", 100))
        except FileNotFoundError:
            pass

    def save_config(self, ip1, ip2, freq, speed, accel):
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "servo_ip_1": ip1,
                "servo_ip_2": ip2,
                "update_frequency": freq,
                "speed": speed,
                "acceleration": accel
            }, f)

    def find_venv_python(self):
            current_dir = Path(__file__).resolve().parent
            for parent in current_dir.parents:
                if (parent / ".venv").exists():
                        return os.path.join(parent, ".venv\Scripts\python.exe")
            # maybe return sys.executable parent, to use target computrers python without .venv?
            raise FileNotFoundError("Could not find project root (containing '.venv' folder)")


    def get_base_path(self):
        if getattr(sys, 'frozen', False):
                # PyInstaller context - return the directory of the executable
                return str(Path(sys.executable).resolve().parent)
        else:
            # Normal context - return the directory of the script
            return os.path.dirname(os.path.abspath(__file__))

    def start_server(self):
        ip1 = self.ip_input1.text().strip()
        ip2 = self.ip_input2.text().strip()
        freq = self.freq_input.value()
        speed = self.speed_input.value()
        accel = self.accel_input.value()

        if not ip1 or not ip2:
            QMessageBox.warning(self, "Input Error", "Please enter valid IP addresses for both servo arms.")
            return

        self.save_config(ip1, ip2, freq, speed, accel)
        
        try:   
            base_path = self.get_base_path()
            if getattr(sys, 'frozen', False):
                server_path = os.path.join(base_path, "palvelin.exe")
                venv_python = None
            else:
                server_path = os.path.join(base_path, "palvelin.py")
                venv_python = self.find_venv_python()
            
            if venv_python:
                cmd = f'"{venv_python}" "{server_path}" --server_left "{ip1}" --server_right "{ip2}" --acc "{accel}" --vel "{speed}"'
            else: 
                cmd = f'"{server_path}" --server_left "{ip1}" --server_right "{ip2}" --acc "{accel}" --vel "{speed}"'

            self.process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )

            self.logger.info(f"Server launched with PID: {self.process.pid}")
            QMessageBox.information(self, "Success", "Server started successfully!")
            self.shutdown_button.setEnabled(True)
            self.start_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")

    def shutdown_server(self):
        try:
            response = requests.get("http://localhost:5001/shutdown")
            a = 10
            if response.returncode == 56:
                QMessageBox.information(self, "Success", "Server shutdown successfully!")
                self.shutdown_button.setEnabled(False)
                self.start_button.setEnabled(True)
            else:
                QMessageBox.warning(self, "Warning", "Failed to shutdown server!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to shutdown server: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith('.py'):
        script_path = sys.argv[1]
        sys.argv = sys.argv[1:]
        runpy.run_path(script_path, run_name='__main__')
    else:
        app = QApplication(sys.argv)
        window = ServerStartupGUI()
        window.show()
        sys.exit(app.exec())


    ### test
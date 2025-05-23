from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox, QTabWidget, QFormLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from utils.setup_logging import setup_logging
from services.WebSocketClientQT import WebsocketClientQT
from widgets.widgets import LabelButtonGroup
import os
import json
import subprocess
import asyncio
import sys
from utils.utils import get_exe_temp_dir,started_from_exe, extract_part, get_current_path, find_venv_python
from pathlib import Path

def get_gui_path():
    return get_current_path().parent / "gui"

def load_styles(self):
    try:
        if started_from_exe():
            temp_file_path = get_exe_temp_dir()
            styles_path = os.path.join(temp_file_path, "src", "gui", "styles.json")
        else: 
            styles_path = get_gui_path() / "styles.json"
        with open(styles_path, "r") as f:
            data = json.load(f)
        
        styles = data["styles"]
        self.styles = {}
        for style in styles:
            for key, val in style.items():
                self.styles[key] = val
    except FileNotFoundError:
        print(f"Error: styles.json not found at {styles_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        
def create_tabs(self):
    # Create Tab Widget
    self.tabs = QTabWidget()
    self.main_layout.addWidget(self.tabs)
    create_general_tab(self)    
    create_advanced_tab(self)
    create_faults_tab(self)
    
def create_server_buttons(self):
    # Start Button
    self.start_button = QPushButton("Start Server")
    self.start_button.clicked.connect(self.handle_button_click)
    self.start_button.setStyleSheet(self.styles["start_up_btn"])
    self.main_layout.addWidget(self.start_button)
    
    # Shutdown Button (Initially Disabled)
    self.shutdown_button = QPushButton("Shutdown Server")
    self.shutdown_button.setEnabled(False)
    self.shutdown_button.clicked.connect(self.shutdown_server)
    self.shutdown_button.setStyleSheet(self.styles["shutdown_btn"])
    self.main_layout.addWidget(self.shutdown_button)
    
def load_config(self):
    try:
        # root = Path(__file__).parent
        # config_path = os.path.join(root, self.self.CONFIG_FILE)
        config_path = "C:\liikealusta\src\gui\config.json"
        with open(config_path, "r") as f:
            config = json.load(f)
            self.ip_input1.setText(config.get("servo_ip_1", ""))
            self.ip_input2.setText(config.get("servo_ip_2", ""))
            self.freq_input.setValue(config.get("update_frequency", 10))
            self.speed_input.setValue(config.get("speed", 50))
            self.accel_input.setValue(config.get("acceleration", 100))
    except FileNotFoundError as e:
        self.logger.error(f"Config file not found: {e}")

def store_current_field_values(self):
    # store initial values of the input fields
        self.stored_values = {
            'ip_input1': self.ip_input1.text(),
            'ip_input2': self.ip_input2.text(),
            'speed_input': self.speed_input.value(),
            'accel_input': self.accel_input.value(),
            'freq_input': self.freq_input.value()
        }
       
def update_stored_values(self):
    self.stored_values = {
            'ip_input1': self.ip_input1.text(),
            'ip_input2': self.ip_input2.text(),
            'speed_input': self.speed_input.value(),
            'accel_input': self.accel_input.value(),
            'freq_input': self.freq_input.value()
        }
    
def update_values(self):
    """Update only the values that have changed."""
    changed_fields = {}
    # Check text fields for changes
    if self.speed_input.value() != self.stored_values['speed_input']:
        changed_fields.update({"velocity": self.speed_input.value()})
        self.logger.info(f"Updating Velocity to {self.speed_input.value()} RPM")      
                
    if self.accel_input.value() != self.stored_values['accel_input']:
        changed_fields.update({"acceleration": self.accel_input.value()})
        self.logger.info(f"Updating Acceleration to {self.accel_input.value()} RPM")   
        
    # Update values based on changes
    if changed_fields:
        # Update stored values after successful update
        self.update_stored_values()
        # Send values to server
        try: ### TODO - muuta tämä lähettämään socket viesti instead
            pass
            # print("TÄSSÄ", response)
        except Exception as e:
            self.logger(f"Error while changing values: {e}")
            
def get_field_values(self):
    ip1 = self.ip_input1.text().strip()
    ip2 = self.ip_input2.text().strip()
    freq = self.freq_input.value()
    speed = self.speed_input.value()
    accel = self.accel_input.value()
    return (ip1, ip2, freq, speed, accel)

def save_config(self, ip1, ip2, freq, speed, accel):
    with open(self.self.CONFIG_FILE, "w") as f:
        json.dump({
            "servo_ip_1": ip1,
            "servo_ip_2": ip2,
            "update_frequency": freq,
            "speed": speed,
            "acceleration": accel
        }, f)

async def clear_fault(self):
    await self.websocket_client.send("action=clearfault|")
    
def create_general_tab(self):
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
    
def create_advanced_tab(self):
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
    
def create_faults_tab(self):
# Fauls tab
    self.faults_tab = QWidget()
    self.faults_layout = QFormLayout()

    # Message Display Label
    self.default_fault_msg_lbl = QLabel("Servo motors have no faults currently")
    self.default_fault_msg_lbl.setWordWrap(True)
    self.default_fault_msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.faults_layout.addWidget(self.default_fault_msg_lbl)
    self.faults_layout.setAlignment(self.default_fault_msg_lbl, Qt.AlignmentFlag.AlignCenter)

    self.fault_group = LabelButtonGroup(styles=self.styles, label_text="msg", button_text="Clear Fault", visible=False)
    self.fault_group.connect_button(self.clear_fault)
    self.faults_layout.addWidget(self.fault_group)

    # Add faults layout to advanced tab
    self.faults_tab.setLayout(self.faults_layout)
    self.tabs.addTab(self.faults_tab, "Faults")

def create_status_label(self):
    self.message_label = QLabel("WebSocket Messages: Not connected")
    self.message_label.setWordWrap(True)
    self.main_layout.addWidget(self.message_label)
    
    create_server_buttons(self)
    set_styles(self)
    
    self.setLayout(self.main_layout)

    # Initialize WebSocket client
    self.websocket_client = WebsocketClientQT(logger=self.logger)
    self.websocket_client.message_received.connect(self.handle_client_message)

    # store initial values of the input fields
    self.stored_values = {
        'ip_input1': self.ip_input1.text(),
        'ip_input2': self.ip_input2.text(),
        'speed_input': self.speed_input.value(),
        'accel_input': self.accel_input.value(),
        'freq_input': self.freq_input.value()
    }

def set_styles(self):
    try:
        if started_from_exe():
            temp_file_path = get_exe_temp_dir()
            styles_path = os.path.join(temp_file_path, "src", "gui", "styles.json")
        else:
            base_path = Path(os.path.abspath(__file__)).parent.parent
            styles_path = os.path.join(base_path, "gui", "styles.json")
        # Load the JSON from the file
        with open(styles_path, "r") as f:
            data = json.load(f)
        for style in data["styles"]:
            if "start_up_btn" in style:
                self.start_button.setStyleSheet(style["start_up_btn"])
            if "shutdown_btn" in style:
                self.shutdown_button.setStyleSheet(style["shutdown_btn"])
    except FileNotFoundError:
        print(f"Error: styles.json not found at {styles_path}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")


def save_config(self, ip1, ip2, freq, speed, accel):
    with open(self.CONFIG_FILE, "w") as f:
        json.dump({
            "servo_ip_1": ip1,
            "servo_ip_2": ip2,
            "update_frequency": freq,
            "speed": speed,
            "acceleration": accel
        }, f)

def get_base_path():
    if started_from_exe():
        return str(Path(sys.executable).resolve().parent)
    else:
        return Path(os.path.abspath(__file__)).parent
    
def update_stored_values(self):
    self.stored_values = {
            'ip_input1': self.ip_input1.text(),
            'ip_input2': self.ip_input2.text(),
            'speed_input': self.speed_input.value(),
            'accel_input': self.accel_input.value(),
            'freq_input': self.freq_input.value()
        }

def handle_button_click(self):
    if not self.is_server_running:
        self.start_server()
    else:
        self.update_values()

def update_values(self):
    """Update only the values that have changed."""
    changed_fields = {}
    # Check text fields for changes
    if self.speed_input.value() != self.stored_values['speed_input']:
        changed_fields.update({"velocity": self.speed_input.value()})
        self.logger.info(f"Updating Velocity to {self.speed_input.value()} RPM")      
                
    if self.accel_input.value() != self.stored_values['accel_input']:
        changed_fields.update({"acceleration": self.accel_input.value()})
        self.logger.info(f"Updating Acceleration to {self.accel_input.value()} RPM")   
        
    # Update values based on changes
    if changed_fields:
        # Update stored values after successful update
        self.update_stored_values()
        # Send values to server
        try: ### TODO - muuta tämä lähettämään socket viesti instead
            pass
            # response = make_request("http://localhost:5001/updatevalues", changed_fields)
            # print("TÄSSÄ", response)
        except Exception as e:
            self.logger(f"Error while changing values: {e}")

def start_server(self):
    ip1 = self.ip_input1.text().strip()
    ip2 = self.ip_input2.text().strip()
    freq = self.freq_input.value()
    speed = self.speed_input.value()
    accel = self.accel_input.value()

    # if not ip1 or not ip2:
    #     QMessageBox.warning(self, "Input Error", "Please enter valid IP addresses for both servo arms.")
    #     return

    self.save_config(ip1, ip2, freq, speed, accel)
    
    try:   
        base_path = get_base_path()
        test = Path(os.path.abspath(__file__)).parent
        if started_from_exe():
            exe_temp_dir = get_exe_temp_dir()
            server_path = os.path.join(exe_temp_dir, "src\motor_api.py")
            self.logger.info(server_path)
            venv_python = "C:\liikealusta\.venv\Scripts\python.exe" # TODO - make this dynamic
        else:
            base_path = Path(base_path).parent
            server_path = os.path.join(base_path, "motor_api.py")
            venv_python = find_venv_python()
        
        if venv_python:
            cmd = f'"{venv_python}" "{server_path}" --server_left "{ip1}" --server_right "{ip2}" --acc "{accel}" --vel "{speed}"'
        else: 
            cmd = f'"{venv_python}" "{server_path}" --server_left "{ip1}" --server_right "{ip2}" --acc "{accel}" --vel "{speed}"'

        self.process = subprocess.Popen(cmd)

        self.logger.info(f"Server launched with PID: {self.process.pid}")
        QMessageBox.information(self, "Success", "Server started successfully!")
        self.shutdown_button.setEnabled(True)
        # self.start_button.setEnabled(False)
        
        # Update inptu values
        self.update_stored_values()
        # Switch button logic to update values
        self.is_server_running = True # server is running
        self.start_button.setText("Update Values")
        # Start WebSocket client after server starts
        asyncio.ensure_future(self.start_websocket_client())
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")

def shutdown_server(self):
    try:
        # First, close the WebSocket client
        loop = asyncio.get_event_loop()
        loop.create_task(self.websocket_client.send("action=shutdown|"))
        # Then attempt to shutdown the server
        ### TODO - muuta tämä lähettämään socket message action instead
        # response = make_request("http://localhost:5001/shutdown")
        # if "success" in response.stdout:  # Fixed: Check status_code, not returncode
        #     QMessageBox.information(self, "Success", "Server shutdown successfully!")
        #     self.shutdown_button.setEnabled(False)
        #     self.start_button.setEnabled(True)
        # else:
        #     QMessageBox.warning(self, "Warning", f"Failed to shutdown server: {response.text}")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to shutdown server: {str(e)}")

def handle_client_message(self, message):
    """Update the GUI label with WebSocket messages."""
    event = extract_part("event=", message=message)
    if not event:
        self.message_label.setText(message)
    elif event == "fault":
        pass

    if "Received: " in message:
        try:
            # Assuming server sends messages like "identity=1|data=value"
            msg_content = message.split("Received: ")[1]
            if "data=" in msg_content:
                value = msg_content.split("data=")[1].split("|")[0]
                # Update GUI based on data (e.g., set speed_input)
                self.speed_input.setValue(int(value))
        except Exception as e:
            self.logger.error(f"Error parsing message: {str(e)}")

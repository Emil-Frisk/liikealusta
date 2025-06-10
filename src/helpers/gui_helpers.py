from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox, QTabWidget, QFormLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from utils.setup_logging import setup_logging
from services.WebSocketClientQT import WebsocketClientQT
from widgets.FaultTab import FaultTab
from widgets.GeneralTab import GeneralTab
from widgets.AdvancedTab import AdvancedTab
import os
import json
import subprocess
import asyncio
import sys
from utils.utils import get_exe_temp_dir,started_from_exe, extract_part, get_current_path, find_venv_python
from pathlib import Path


def load_styles(self):
    try:
        if started_from_exe():
            temp_file_path = get_exe_temp_dir()
            styles_path = os.path.join(temp_file_path, "src", "gui", "styles.json")
        else: 
            styles_path = self.path / "styles.json"
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
        config_path = self.CONFIG_FILE
        with open(config_path, "r") as f:
            config = json.load(f)
            self.advanced_tab.set_left_motor(config.get("servo_ip_1", ""))
            self.advanced_tab.set_right_motor(config.get("servo_ip_2", ""))
            self.advanced_tab.set_freq(config.get("update_frequency", 10))
            self.general_tab.set_velocity(config.get("speed", 50))
            self.general_tab.set_acceleration(config.get("acceleration", 100))
    except FileNotFoundError as e:
        self.logger.error(f"Config file not found: {e}")

def store_current_field_values(self):
    # store initial values of the input fields
        self.stored_values = {
            'ip_input1': self.advanced_tab.get_left_motor(),
            'ip_input2': self.advanced_tab.get_right_motor(),
            'speed_input': self.general_tab.get_velocity(),
            'accel_input': self.general_tab.get_acceleration(),
            'freq_input': self.advanced_tab.get_freq()
        }
       
def update_stored_values(self):
    store_current_field_values(self)
    
def get_field_values(self):
    ip1 = self.advanced_tab.get_left_motor().strip()
    ip2 = self.advanced_tab.get_right_motor().strip()
    freq = self.advanced_tab.get_freq()
    speed = self.general_tab.get_velocity()
    accel = self.general_tab.get_acceleration()
    return (ip1, ip2, freq, speed, accel)

async def clear_fault(self):
    await self.websocket_client.send("action=clearfault|")
    
def create_general_tab(self):
    # General Tab
    self.general_tab = GeneralTab()
    self.tabs.addTab(self.general_tab, "General")
    
def create_advanced_tab(self):
   # Advanced Tab
    self.advanced_tab = AdvancedTab()
    self.tabs.addTab(self.advanced_tab, "Advanced")
    
def create_faults_tab(self):
# Fauls tab
    self.faults_tab = FaultTab(styles=self.styles, clear_fault_cb=self.clear_fault)
    self.tabs.addTab(self.faults_tab, "Faults")

def create_status_label(self):
    self.message_label = QLabel("WebSocket Messages: Not connected")
    self.message_label.setWordWrap(True)
    self.main_layout.addWidget(self.message_label)
    
    set_styles(self)
    
    self.setLayout(self.main_layout)

    # Initialize WebSocket client
    self.websocket_client = WebsocketClientQT(logger=self.logger)
    self.websocket_client.message_received.connect(self.handle_client_message)

    # store initial values of the input fields
    self.stored_values = {
        'ip_input1': self.advanced_tab.get_left_motor(),
        'ip_input2': self.advanced_tab.get_right_motor(),
        'speed_input': self.general_tab.get_velocity(),
        'accel_input': self.general_tab.get_acceleration(),
        'freq_input': self.advanced_tab.get_freq()
    }

def set_styles(self):
    try:
        if started_from_exe():
            temp_file_path = get_exe_temp_dir()
            styles_path = os.path.join(temp_file_path, "src", "gui", "styles.json")
        else:
            styles_path = self.styles_path

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

    
def start_server(self):
    (ip1, ip2, freq, speed, accel)  = get_field_values(self)

    if not ip1 or not ip2:
        QMessageBox.warning(self, "Input Error", "Please enter valid IP addresses for both servo arms.")
        return

    save_config(self, ip1, ip2, freq, speed, accel)
    
    try:
        ### Make sure the process main.py is not already running for some reason
        result = self.process_manager.exterminate_lingering_process("main")
        if not result:
            self.logger.error(f"Unable to kill lingering process with name: main. Not launching a new process...")
            return
        elif result:
            self.logger.info(f"No lingering process remaining.")
        
        self.process_manager.launch_process("main", args=["--server_left", ip1, "--server_right", ip2, "--acc", str(accel), "--vel", str(speed)])

        # Start WebSocket client after server starts
        self.start_websocket_client()
        self.start_button.setEnabled(False)
    except FileNotFoundError as e:
        self.logger.error(f"Could not find venv: {e}")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")


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



def findProcessByName(processname):
    """
    Finds process by given name. Returns result object. 
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", f"Get-Process -Name {processname} -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True
        )
        return result
    except:
        raise
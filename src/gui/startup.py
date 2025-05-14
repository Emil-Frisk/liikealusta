import sys
import json
import os
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QSpinBox, QTabWidget, QFormLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal, QObject
import requests
import asyncio
import websockets
import qasync
from utils.setup_logging import setup_logging

CONFIG_FILE = "config.json"

class WebSocketClient(QObject):
    # Signal to emit received messages to the GUI
    message_received = pyqtSignal(str)

    def __init__(self,logger, uri="ws://localhost:6969"):
        super().__init__()
        self.uri = uri
        self.logger = logger
        self.websocket = None
        self.running = False
        self.loop = None

    async def connect(self):
        """Connect to the WebSocket server and listen for messages."""
        try_count = 0
        max_tries = 10
        while try_count < max_tries:
            try:
                self.websocket = await websockets.connect(self.uri)
                self.running = True
                self.message_received.emit(f"Connected to {self.uri}")
                await self.listen()
            except ConnectionRefusedError as e:
                self.logger.error(f"Server not up yet; connection error: {str(e)}, attempt: {try_count}/{max_tries} trying again soon")
                try_count += 1
                await asyncio.sleep(5)
            except Exception as e:
                try_count +=1
                self.logger(f"Client connection error: {str(e)}, attempt: {try_count}/{max_tries} trying again soon")
                await asyncio.sleep(5)
        
        self.message_received.emit(f"Client failed to connect to websocket server after max tries...")
        self.running = False

    async def listen(self):
        """Listen for incoming messages."""
        ## TODO - implement recovery
        try:
            async for message in self.websocket:
                self.message_received.emit(f"Received: {message}")
        except websockets.ConnectionClosed as e:
            self.message_received.emit(f"WebSocket disconnected: {e}")
            self.connect()
            self.running = False
        except Exception as e:
            self.connect()
            self.message_received.emit(f"WebSocket error: {str(e)}")
            self.running = False

    async def send(self, message):
        """Send a message to the server."""
        if self.websocket and self.running:
            try:
                await self.websocket.send(message)
                self.message_received.emit(f"Sent: {message}")
            except Exception as e:
                self.message_received.emit(f"Failed to send message: {str(e)}")

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            try:
                await self.websocket.close()
                self.message_received.emit("WebSocket connection closed")
                self.running = False
            except Exception as e:
                self.message_received.emit(f"Error closing WebSocket: {str(e)}")

class ServerStartupGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = setup_logging("startup", "startup.log")
        self.project_root = ""
        
        self.setWindowTitle("Server Startup")
        self.setGeometry(100, 100, 400, 400)  # Adjusted height for message label
        
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

        # Message Display Label
        self.message_label = QLabel("WebSocket Messages: Not connected")
        self.message_label.setWordWrap(True)
        self.main_layout.addWidget(self.message_label)

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

        # Initialize WebSocket client
        self.websocket_client = WebSocketClient(logger=self.logger)
        self.websocket_client.message_received.connect(self.update_message_label)

    def set_styles(self):
        styles_path = os.path.join(Path(__file__).parent, "styles.json")
        try:
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
                return os.path.join(parent, ".venv", "Scripts", "python.exe")
        raise FileNotFoundError("Could not find project root (containing '.venv' folder)")

    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            return str(Path(sys.executable).resolve().parent)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    async def start_websocket_client(self):
        """Start the WebSocket client."""
        await self.websocket_client.connect()

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

            # Start WebSocket client after server starts
            asyncio.ensure_future(self.start_websocket_client())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")

    async def shutdown_websocket_client(self):
        """Shutdown the WebSocket client."""
        await self.websocket_client.close()

    def shutdown_server(self):
        try:
            # First, close the WebSocket client
            asyncio.run_coroutine_threadsafe(self.shutdown_websocket_client(), qasync.get_event_loop())

            # Then attempt to shutdown the server
            response = requests.get("http://localhost:5001/shutdown")
            if response.status_code == 200:  # Fixed: Check status_code, not returncode
                QMessageBox.information(self, "Success", "Server shutdown successfully!")
                self.shutdown_button.setEnabled(False)
                self.start_button.setEnabled(True)
            else:
                QMessageBox.warning(self, "Warning", f"Failed to shutdown server: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to shutdown server: {str(e)}")

    def update_message_label(self, message):
        """Update the GUI label with WebSocket messages."""
        self.message_label.setText(message)

        # Example: Parse message and update GUI elements
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Initialize qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = ServerStartupGUI()
    window.show()
    
    with loop:
        loop.run_forever()
import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication, QWidget, QWidget, QVBoxLayout, QLabel,QMessageBox
from PyQt6.QtGui import QFont
from utils.setup_logging import setup_logging
from services.WebSocketClientQT import WebsocketClientQT
import os
import subprocess
from utils.utils import get_exe_temp_dir,find_venv_python,started_from_exe, get_base_path, get_current_path, extract_part
from helpers import gui_helpers as helpers
from pathlib import Path

class ServerStartupGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = setup_logging("startup", "startup.log")
        self.is_server_running = False
        self.setWindowTitle("Server Startup")
        self.setGeometry(100, 100, 400, 400) 
        self.styles_path = helpers.get_gui_path() / "styles.json"
        self.CONFIG_FILE = helpers.get_gui_path() / "config.json"
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        font = QFont("Arial", 14)
        self.setFont(font)
        
        helpers.load_styles(self)
        helpers.create_tabs(self)
        helpers.load_config(self)
        helpers.create_server_buttons(self)
        helpers.create_status_label(self)
        helpers.store_current_field_values(self)
        
        self.faults_tab.update_fault_message("test")

        # Initialize WebSocket client
        self.websocket_client = WebsocketClientQT(identity="gui", logger=self.logger)
        self.websocket_client.message_received.connect(self.handle_client_message)

    def start_websocket_client(self):
        """Start the WebSocket client."""
        asyncio.create_task(self.websocket_client.connect())
        
    def handle_button_click(self):
        if not self.is_server_running:
            self.start_server()
        else:
            helpers.update_values()
    
    def start_server(self):
        (ip1, ip2, freq, speed, accel)  = helpers.get_field_values(self)
        a=10

        if not ip1 or not ip2:
            QMessageBox.warning(self, "Input Error", "Please enter valid IP addresses for both servo arms.")
            return

        helpers.save_config(self, ip1, ip2, freq, speed, accel)
        
        try:   
            base_path = get_base_path()
            if started_from_exe():
                exe_temp_dir = get_exe_temp_dir()
                server_path = os.path.join(exe_temp_dir, "src\main.py")
                self.logger.info(server_path)
                venv_python = "C:\liikealusta\.venv\Scripts\python.exe" # TODO - make this dynamic
            else:
                server_path = os.path.join(base_path, "main.py")
                venv_python = find_venv_python()
            
            if venv_python:
                cmd = f'"{venv_python}" "{server_path}" --server_left "{ip1}" --server_right "{ip2}" --acc "{accel}" --vel "{speed}"'
            else: 
                cmd = f'"{venv_python}" "{server_path}" --server_left "{ip1}" --server_right "{ip2}" --acc "{accel}" --vel "{speed}"'

            self.process = subprocess.Popen(cmd)

            self.logger.info(f"Server launched with PID: {self.process.pid}")
            QMessageBox.information(self, "Success", "Server started successfully!")
            self.start_button.setEnabled(False)
            
            # Update inptu values
            helpers.update_stored_values(self)
            # Switch button logic to update values
            self.start_button.setText("Update Values")
            # Start WebSocket client after server starts
            self.start_websocket_client()
        except FileNotFoundError as e:
            self.logger.error(f"Could not find venv: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start server: {str(e)}")
        
    def shutdown_websocket_client(self):
        """Shutdown the WebSocket client."""
        asyncio.create_task(self.websocket_client.close())

    def shutdown_server(self):
        try:
            # First, close the WebSocket client
            loop = asyncio.get_event_loop()
            loop.create_task(self.websocket_client.send("action=shutdown|"))
            self.start_button.setText("Start Server")
            self.start_button.setEnabled(False)
            self.shutdown_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to shutdown server: {str(e)}")

    def handle_client_message(self, message):
        """Update the GUI label with WebSocket messages."""
        event = extract_part("event=", message=message)
        clientmessage = extract_part("message=", message=message)
        if not event:
            self.logger.error("No event specified in message.")
            return
        if not clientmessage: 
            self.logger.error("No client message specified in message.")
            return
        elif event == "error":
            self.logger.error(message)
        elif event == "fault":
            self.logger.warning("Fault event has arrived to GUI!")
            QMessageBox.warning(self, "Error", clientmessage+"\n Check faults tab for more info")
            self.faults_tab.update_fault_message(clientmessage)
            self.faults_tab.toggle_component_visibility()
        elif event == "faultcleared":
            self.logger.info("Fault cleared event has reached gui")
            QMessageBox.information(self, "Info", "fault was cleared successfully")
            self.faults_tab.toggle_component_visibility()
        elif event == "connected":
            self.shutdown_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.is_server_running = True # server is running
            self.message_label.setText(clientmessage)
        elif event == "shutdown":
            self.is_server_running = False
            self.start_button.setEnabled(True)
            self.shutdown_button.setEnabled(False)
            self.faults_tab.hide_fault()
    
    def clear_fault(self):
        asyncio.create_task(helpers.clear_fault(self))

    def fault_reset(self):
        pass ### TODO - jatka tästä
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Initialize qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = ServerStartupGUI()
    window.show()
    
    with loop:
        loop.run_forever()
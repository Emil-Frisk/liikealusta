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
from services.process_manager import ProcessManager

class ServerStartupGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = setup_logging("startup", "startup.log")
        self.process_manager = ProcessManager(logger=self.logger, target_dir=get_current_path(__file__).parent)
        self.setWindowTitle("Server Startup")
        self.setGeometry(100, 100, 400, 400) 
        self.path = Path(__file__).parent
        self.styles_path = self.path / "styles.json"
        self.CONFIG_FILE = self.path / "config.json"
        
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
        helpers.start_server(self)
        
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
            self.faults_tab.show_fault_group()
        elif event == "absolute_fault":
            QMessageBox.warning(self, "Error", "Absolute fault has occured! DO NOT continue using the motors anymore, they need some serious maintance.")
        elif event == "faultcleared":
            self.logger.info("Fault cleared event has reached gui")
            QMessageBox.information(self, "Info", "fault was cleared successfully")
            self.faults_tab.hide_fault_group()
        elif event == "motors_initialized":
            self.shutdown_button.setEnabled(True)
            QMessageBox.information(self, "Info", "Motors have been initialized successfully")
        elif event == "connected":
            self.message_label.setText(clientmessage)
        elif event == "shutdown":
            self.start_button.setEnabled(True)
            self.shutdown_button.setEnabled(False)
            self.faults_tab.hide_fault()
    
    def clear_fault(self):
        asyncio.create_task(helpers.clear_fault(self))    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Initialize qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    # TODO Tarkista onko mevea prosesseja päällä
    window = ServerStartupGUI()
    window.show()
    
    with loop:
        loop.run_forever()
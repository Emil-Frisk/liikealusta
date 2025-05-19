import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication, QWidget
import services.gui_service as gui_service

CONFIG_FILE = "config.json"

class ServerStartupGUI(QWidget):
    def __init__(self):
        super().__init__()
        gui_service.init_gui(self)
        self.fault_group.set_label_text("what")

    def set_styles(self):
        gui_service.set_styles(self)
        
    def load_config(self):
        gui_service.load_config(self)

    def save_config(self, ip1, ip2, freq, speed, accel):
        gui_service.save_config(ip1, ip2, freq, speed, accel)

    def get_base_path(self):
        gui_service.get_base_path()

    async def start_websocket_client(self):
        """Start the WebSocket client."""
        await self.websocket_client.connect()
        
    def update_stored_values(self):
        gui_service.update_stored_values(self)

    def handle_button_click(self):
        gui_service.handle_button_click(self)
        
    def update_values(self):
        gui_service.update_values(self)
    
    def start_server(self):
        gui_service.start_server(self)
        
    async def shutdown_websocket_client(self):
        """Shutdown the WebSocket client."""
        await self.websocket_client.close()

    def shutdown_server(self):
        gui_service.shutdown_server()

    def handle_client_message(self, message):
        gui_service.handle_client_message(self, message=message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Initialize qasync event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = ServerStartupGUI()
    window.show()
    
    with loop:
        loop.run_forever()
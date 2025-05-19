from PyQt6.QtCore import pyqtSignal, QObject
import websockets
import asyncio

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
                break
            except ConnectionRefusedError as e:
                self.logger.error(f"Server not up yet; connection error: {str(e)}, attempt: {try_count}/{max_tries} trying again soon")
                try_count += 1
                await asyncio.sleep(5)
            except Exception as e:
                try_count +=1
                self.logger(f"Client connection error: {str(e)}, attempt: {try_count}/{max_tries} trying again soon")
                await asyncio.sleep(5)
        
        if not self.running:
            self.message_received.emit(f"Client failed to connect to websocket server after max tries...")
            self.running = False

    async def send(self, message):
        """Send a message to the server."""
        if self.websocket and self.running:
            try:
                await self.websocket.send(message)
                self.message_received.emit(f"Sent: {message}")
            except Exception as e:
                self.message_received.emit(f"Failed to send message: {str(e)}")

    async def listen(self):
        """Listen for incoming messages."""
        try:
            async for message in self.websocket:
                self.message_received.emit(f"Received: {message}")
        except websockets.ConnectionClosed as e:
            self.message_received.emit(f"WebSocket disconnected: {e}")
            await self.connect()
            self.running = False
        except Exception as e:
            await self.connect()
            self.message_received.emit(f"WebSocket error: {str(e)}")
            self.running = False

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            try:
                await self.websocket.close()
                self.message_received.emit("WebSocket connection closed")
                self.running = False
            except Exception as e:
                self.message_received.emit(f"Error closing WebSocket: {str(e)}")
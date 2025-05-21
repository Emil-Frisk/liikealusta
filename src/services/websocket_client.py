import asyncio
import websockets
from websockets.exceptions import ConnectionClosed

class WebsocketClient():
    def __init__(self, logger, identity="unknown", uri="ws://localhost:6969", on_message=None, reconnect_interval = 10, max_reconnect_attempt=5):
        self.uri = uri
        self.socket = None
        self.is_running = False
        self.on_message = on_message
        self._listen_task = None
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempt = max_reconnect_attempt
        self.reconnect_count  = 0
        self.logger = logger
        self.identity = identity
    
    async def connect(self):
        try:
            if self.is_running:
                self.logger.info("Client is already connected, can't connect again")
                return 
            
            self.socket = await asyncio.wait_for(websockets.connect(self.uri, ping_timeout=None), timeout=10) 
            ### identify client to the server
            await self.socket.send(f"action=identify|identity={self.identity}|")
            self.is_running = True
            self.reconnect_count = 0
            self.logger.info(f"client connected to server: {self.uri}")
            self._listen_task = asyncio.create_task(self._listen())
        except TimeoutError:
            await self.handle_connection_failure(f"Connection timed out after 10 seconds")
        except Exception as e:
            await self.handle_connection_failure(f"Error connecting to the server: {e}")
    
    async def handle_connection_failure(self, error_msg):
        """Handle a connection failure by scheduling a reconnect or closing the client."""
        self.logger.error(f"Connection failed: {error_msg}")
        self.reconnect_count += 1
        if self.reconnect_count < self.max_reconnect_attempt:
            await self._schedule_reconnect()
        else:
            self.logger.info("Maximum reconnect attempts reached, closing client")
            await self.close()
    
    async def _listen(self):
        try:
            self.logger.info("Creating listening coroutine for client")
            while self.is_running:
                response = await self.socket.recv()
                if self.on_message:
                    self.on_message(response)
        except ConnectionClosed:
            self.logger.info("Client disconnected from the server")
        except Exception as e:
            self.logger.error(f"Exception in the listen coroutine: {e}")
        finally:
            if self.is_running:
                self.is_running = False
                if self.reconnect_count < self.max_reconnect_attempt:
                    await self._schedule_reconnect()

    async def _schedule_reconnect(self):
        await asyncio.sleep(self.reconnect_interval)
        await self.connect()

    async def send(self, message):
        try:
            if not self.is_running or self.socket == None:
                self.logger.info("Client not connected, can't send a mesasge")
                return

            await self.socket.send(message)
            return True
        except Exception as e:
            self.logger.error(f"Error while client was sending a message: {e}")
            return False

    async def close(self):
        try:
            self.is_running = False
            if self._listen_task:
                self._listen_task.cancel()
                try: 
                    await self._listen_task
                except asyncio.CancelledError:
                    pass
                self._listen_task = None

            if self.socket:
                await self.socket.close()
        except Exception as e:
            self.logger.error(f"Exception while closing down a client {e}")
        finally:
            self.socket = None
            self.logger.info("client socket closed")
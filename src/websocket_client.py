import asyncio
import websockets
from websockets.exceptions import ConnectionClosed

class WebsocketClient():
    def __init__(self, uri="ws://localhost:6969", on_message=None, reconnect_interval = 5, max_reconnect_attempt=2, logger=logger):
        self.uri = uri
        self.socket = None
        self.is_running = False
        self.on_message = on_message
        self._listen_task = None
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempt = max_reconnect_attempt
        self.reconnect_count  = 0
    
    async def connect(self):
        try:
            if self.is_running:
                print("Client is already connected, can't connect again")
                return 
            
            self.socket = await asyncio.wait_for(websockets.connect(self.uri), timeout=10) 
            self.is_running = True
            self.reconnect_count = 0
            print(f"client connected to server: {self.uri}")
            self._listen_task = asyncio.create_task(self._listen())
        except TimeoutError:
            await self.handle_connection_failure(f"Connection timed out after 10 seconds")
        except Exception as e:
            await self.handle_connection_failure(f"Error connecting to the server: {e}")
    
    async def handle_connection_failure(self, error_msg):
        """Handle a connection failure by scheduling a reconnect or closing the client."""
        print(f"Connection failed: {error_msg}")
        self.reconnect_count += 1
        if self.reconnect_count < self.max_reconnect_attempt:
            await self._schedule_reconnect()
        else:
            print("Maximum reconnect attempts reached, closing client")
            await self.close()
    
    async def _listen(self):
        try:
            print("Creating listening coroutine for client")
            while self.is_running:
                response = await self.socket.recv()
                if self.on_message:
                    self.on_message(response)
        except ConnectionClosed:
            print("Client disconnected from the server")
        except Exception as e:
            print(e)
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
                print("Client not connected, can't send a mesasge")
                return

            await self.socket.send(message)
            return True
        except Exception as e:
            print(e)
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
            print(e)
        finally:
            self.socket = None
            print("client socket closed")

# def on_message(msg):
#     print(f"Message callback fired: {msg}")

# async def main():
#     client = WebsocketClient(on_message=on_message)
#     await client.connect()
#     try:
        
#         while True:
#             print("Hello from the main function")
#             await asyncio.sleep(5)
#     except KeyboardInterrupt:
#         print("shutting down the client")
#     finally:
#         await client.close()

# if __name__ == "__main__":
#     asyncio.run(main())
import asyncio
import websockets
from utils.utils import extract_identity, extract_receiver

class CommunicationHub:
    def __init__(self):
        self.clients = {}

    async def handle_client(self, websocket, path=None):
        # Store client metadata
        client_info = {"identity": "unknown"}
        self.clients[websocket] = client_info
        print(f"Client {websocket.remote_address} connected! Path: {path or '/'}", flush=True)

        try:
            async for message in websocket:
                print(f"Received: {message}", flush=True)
                identity = extract_identity(message)
                if identity:
                    client_info["identity"] = identity
                    print(f"Updated identity for {websocket.remote_address}: {identity}", flush=True)

                receiver = extract_receiver(message)
                if receiver:
                    print(f"Receiver: {receiver}", flush=True)

                # Send response to clients with identity "1"
                response = "Message received"
                for client, info in self.clients.items():
                    if info["identity"] == "1":
                        await client.send(response)

        except websockets.ConnectionClosed as e:
            print(f"Client {websocket.remote_address} (identity: {client_info['identity']}) disconnected with code {e.code}, reason: {e.reason}", flush=True)
        except Exception as e:
            print(f"Unexpected error for client {websocket.remote_address} (identity: {client_info['identity']}): {e}", flush=True)
        finally:
            print(f"Cleaning up for client {websocket.remote_address} (identity: {client_info['identity']})", flush=True)
            del self.clients[websocket]

    async def start_server(self):
        server = await websockets.serve(self.handle_client, "localhost", 6969)
        print("WebSocket server running on ws://localhost:6969")
        await server.wait_closed()

async def main():
    hub = CommunicationHub()
    await hub.start_server()

if __name__ == "__main__":
    asyncio.run(main())
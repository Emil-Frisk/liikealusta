import asyncio
import websockets
from utils.utils import extract_part



class CommunicationHub:
    def __init__(self):
        self.clients = {}

    def extract_parts(self, message):
        receiver = extract_part("receiver=", message=message)
        identity = extract_part("identity=", message=message)
        message = extract_part("message=", message=message)
        return (identity, receiver, message)

    async def handle_client(self, websocket, path=None):
        # Store client metadata
        client_info = {"identity": "unknown"}
        self.clients[websocket] = client_info
        print(f"Client {websocket.remote_address} connected! Path: {path or '/'}", flush=True)

        try:
            async for message in websocket:
                print(f"Received: {message}", flush=True)
                (receiver, identity, message) = self.extract_parts()
                if identity:
                    client_info["identity"] = identity
                    print(f"Updated identity for {websocket.remote_address}: {identity}", flush=True)

                if receiver:
                    print(f"Receiver: {receiver}", flush=True)

                # Send response to clients with identity receiver
                for client, info in self.clients.items():
                    if info["identity"] == receiver:
                        await client.send(message)

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
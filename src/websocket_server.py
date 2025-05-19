import asyncio
import atexit
import websockets
from ModbusClients import ModbusClients
from launch_params import handle_launch_params
from module_manager import ModuleManager
from services.cleaunup import cleanup
from services.monitor_service import create_hearthbeat_monitor_tasks
from services.motor_service import configure_motor
from utils.setup_logging import setup_logging
from utils.utils import extract_part



class CommunicationHub:
    def __init__(self):
        self.wsclients = {}
        self.logger = setup_logging("server", "server.log")
        self.module_manage = ModuleManager(self.logger)
        self.config = handle_launch_params()
        self.clients = ModbusClients(self.config, self.logger)
        self.is_process_done = False
    async def init(self):
        try:
            await create_hearthbeat_monitor_tasks(self, self.module_manage)
            # Connect to both drivers
            connected = await self.clients.connect() 
            
            if not connected:  
                self.logger.error(f"""could not form a connection to both motors,
                            Left motors ips: {self.config.SERVER_IP_LEFT}, 
                            Right motors ips: {self.config.SERVER_IP_RIGHT}, 
                            shutting down the server """)
                cleanup(self)
            self.is_process_done = True

            atexit.register(lambda: cleanup(self))
            await configure_motor(self.clients, self.config)
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")


    def extract_parts(self, message): # example message: "receiver=startup|identity=fault_poller|message=CRITICAL FAULT!"
        receiver = extract_part("receiver=", message=message)
        identity = extract_part("identity=", message=message)
        message = extract_part("message=", message=message)

        return (identity, receiver, message)
    
    async def handle_client(self, websocket, path=None):
        # Store client metadata
        client_info = {"identity": "unknown"}
        self.wsclients[websocket] = client_info
        print(f"Client {websocket.remote_address} connected! Path: {path or '/'}", flush=True)

        try:
            async for message in websocket:
                print(f"Received: {message}", flush=True)
                (receiver, identity, message) = self.extract_parts(message)
                if identity:
                    client_info["identity"] = identity
                    print(f"Updated identity for {websocket.remote_address}: {identity}", flush=True)
                if receiver:
                    print(f"Receiver: {receiver}", flush=True)

                # "endpoints"
                if message == "write":
                    pass
                if message == "shutdown":
                    pass
                if message == "stop":
                    pass
                if message == "setvalues":
                    pass
                if message == "updatevalues":
                    pass
                    
                # Send response to clients with identity receiver
                for client, info in self.wsclients.items():
                    if info["identity"] == receiver:
                        await client.send(message)
                

        except websockets.ConnectionClosed as e:
            print(f"Client {websocket.remote_address} (identity: {client_info['identity']}) disconnected with code {e.code}, reason: {e.reason}", flush=True)
        except Exception as e:
            print(f"Unexpected error for client {websocket.remote_address} (identity: {client_info['identity']}): {e}", flush=True)
        finally:
            print(f"Cleaning up for client {websocket.remote_address} (identity: {client_info['identity']})", flush=True)
            del self.wsclients[websocket]

    async def start_server(self):
        server = await websockets.serve(self.handle_client, "localhost", 6969)
        print("WebSocket server running on ws://localhost:6969")
        await server.wait_closed()

async def main():
    hub = CommunicationHub()
    await hub.start_server()

if __name__ == "__main__":
    asyncio.run(main())
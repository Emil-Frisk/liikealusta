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
from services.websocket_methods import shutdown,stop_motors,calculate_pitch_and_roll,update_input_values,demo_control
import services.validation_service as validation_service

class CommunicationHub:
    def __init__(self):
        self.wsclients = {}
        self.logger = setup_logging("server", "server.log")
        self.module_manage = ModuleManager(self.logger)
        self.config = handle_launch_params()
        self.clients = ModbusClients(self.config, self.logger)
        self.is_process_done = False
        self.server = None
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


    def extract_parts(self, message): # example message: "action=STOP|receiver=startup|identity=fault_poller|message=CRITICAL FAULT!|pitch=40.3"
        receiver = extract_part("receiver=", message=message)
        identity = extract_part("identity=", message=message)
        message = extract_part("message=", message=message)
        action = extract_part("action=", message=message)
        pitch = extract_part("pitch=", message=message)
        roll = extract_part("roll=", message=message)
        acceleration = extract_part("acc=", message=message)
        velocity = extract_part("vel", message=message)

        return (identity, receiver, message,action,pitch,roll,acceleration,velocity)
    
    async def handle_client(self, wsclient, path=None):
        # Store client metadata
        client_info = {"identity": "unknown"}
        self.wsclients[wsclient] = client_info
        print(f"Client {wsclient.remote_address} connected! Path: {path or '/'}", flush=True)

        try:
            async for message in wsclient:
                print(f"Received: {message}", flush=True)
                (receiver, identity, message,action,pitch,roll,acceleration,velocity) = self.extract_parts(message)
                if not action:
                    wsclient.send("No action given, example action=<action>")
                else: 
                    if identity:
                        client_info["identity"] = identity
                        print(f"Updated identity for {wsclient.remote_address}: {identity}", flush=True)
                    if receiver:
                        print(f"Receiver: {receiver}", flush=True)
                    
                    # "endpoints"
                    if action == "write":
                        result = validation_service.validate_pitch_and_roll_values(pitch,roll)
                        if result:
                            await demo_control(pitch, roll, self)
                            
                    if action == "shutdown":
                        result = await shutdown(self)
                        
                    if action == "stop":
                        result = await stop_motors(self)
                        
                    if action == "setvalues":
                        try:
                            result = validation_service.validate_pitch_and_roll_values(pitch, roll)
                            if result:
                                calculate_pitch_and_roll(pitch,roll)
                        except ValueError as e:
                            self.logger.error(f"ValueError: {e}")
                            print(f"ValueError: {e}")
                        except Exception as e:
                            self.logger.error(f"Error while setting values: {e}")
                            print(f"Error while setting values: {e}")

                    if action == "updatevalues":
                        result = await update_input_values(self,acceleration,velocity)
                        
                    if action == "message":
                        (result, msg) = validation_service.validate_message(self,receiver,message)
                        if result:
                            receiver.send(msg)
                        else:
                            wsclient.send(msg)

        except websockets.ConnectionClosed as e:
            print(f"Client {wsclient.remote_address} (identity: {client_info['identity']}) disconnected with code {e.code}, reason: {e.reason}", flush=True)
        except Exception as e:
            print(f"Unexpected error for client {wsclient.remote_address} (identity: {client_info['identity']}): {e}", flush=True)
        finally:
            print(f"Cleaning up for client {wsclient.remote_address} (identity: {client_info['identity']})", flush=True)
            del self.wsclients[wsclient]

    async def start_server(self):
        self.server = await websockets.serve(self.handle_client, "localhost", 6969)
        print("WebSocket server running on ws://localhost:6969")

async def main():
    hub = CommunicationHub()
    await hub.init()
    await hub.start_server()


async def shutdown_ws_server(self):
    if hasattr(self, "server") and self.server != None:
        try:
            self.logger.info("Closing websocket server...")
            self.server.close()
            self.server.wait_closed()
            self.logger.info("Websocket server closed successfully.")
        except Exception as e:
            print("Error closing webosocket server.")
            self.logger.error("Error while closing the websocket server.")
            
        
if __name__ == "__main__":
    asyncio.run(main())
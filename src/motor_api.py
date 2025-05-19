import asyncio
import atexit
import os
import websockets
from ModbusClients import ModbusClients
from services.module_manager import ModuleManager
from services.cleaunup import cleanup
from services.monitor_service import create_hearthbeat_monitor_tasks
from services.motor_service import configure_motor
from utils.launch_params import handle_launch_params
from utils.setup_logging import setup_logging
from utils.utils import extract_part
from services.websocket_methods import shutdown,stop_motors,calculate_pitch_and_roll,update_input_values,demo_control
import services.validation_service as validation_service

class CommunicationHub:
    def __init__(self):
        self.wsclients = {}
        self.logger = setup_logging("server", "server.log")
        self.module_manager = ModuleManager(self.logger)
        self.config = handle_launch_params()
        self.clients = ModbusClients(self.config, self.logger)
        self.is_process_done = False
        self.server = None
    async def init(self):
        try:
            await create_hearthbeat_monitor_tasks(self, self.module_manager)
            # Connect to both drivers
            connected = await self.clients.connect() 
            
            if not connected:
                self.logger.error(f"""could not form a connection to both motors,
                            Left motors ips: {self.config.SERVER_IP_LEFT}, 
                            Right motors ips: {self.config.SERVER_IP_RIGHT}, 
                            shutting down the server """)
                await cleanup(self)
            self.is_process_done = True

            atexit.register(lambda: cleanup(self))
            await configure_motor(self.clients, self.config)
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")


    def extract_parts(self, msg): # example message: "action=STOP|receiver=startup|identity=fault_poller|message=CRITICAL FAULT!|pitch=40.3"
        receiver = extract_part("receiver=", message=msg)
        identity = extract_part("identity=", message=msg)
        message = extract_part("message=", message=msg)
        action = extract_part("action=", message=msg)
        pitch = extract_part("pitch=", message=msg)
        roll = extract_part("roll=", message=msg)
        acceleration = extract_part("acc=", message=msg)
        velocity = extract_part("vel=", message=msg)

        return (receiver, identity, message,action,pitch,roll,acceleration,velocity)
    
    async def shutdown_ws_server(self):
        if hasattr(self, "server") and self.server != None:
            try:
                self.logger.info("Closing websocket server...")
                self.server.close()

                await asyncio.wait_for(self.server.wait_closed(),5)

                self.logger.info("Websocket server closed successfully.")
            except TimeoutError:
                os._exit(0) 
            except Exception as e:
                print("Error closing webosocket server.")
                self.logger.error("Error while closing the websocket server.")
                os._exit(0) 

    async def handle_client(self, wsclient, path=None):
        # Store client metadata
        client_info = {"identity": "unknown"}
        self.wsclients[wsclient] = client_info
        print(f"Client {wsclient.remote_address} connected! Path: {path or '/'}", flush=True)

        try:
            async for message in wsclient:
                print(f"Received: {message}")
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
                            
                    elif action == "shutdown":
                        result = await shutdown(self)
                        
                    elif action == "stop":
                        result = await stop_motors(self)
                        
                    elif action == "setvalues":
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

                    elif action == "updatevalues":
                        result = await update_input_values(self,acceleration,velocity)
                        
                    elif action == "message":
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
            await self.cleanup_client()

    async def cleanup_client(self, client_socket):
        print(f"Cleaning up client: {client_socket.remote_address} (identity: {self.clients[client_socket]["identity"]})")
        if client_socket in self.clients:
            del self.clients[client_socket]
        try:
            await client_socket.close()
        except Exception as e:
            print(f"Error closing connection for {client_socket.remote_address}: {e}", flush=True)

    async def start_server(self):
        self.server = await websockets.serve(self.handle_client, "localhost", 6969)
        print("WebSocket server running on ws://localhost:6969")

async def main():
    try:
        hub = CommunicationHub()
        await hub.init()
        await hub.start_server()
        while True:
            await asyncio.sleep(10)

    except KeyboardInterrupt:
        print("asd")
    finally:
        await shutdown(hub)
        
if __name__ == "__main__":
    asyncio.run(main())
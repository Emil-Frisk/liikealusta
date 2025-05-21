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
        event = extract_part("event=", message=msg)
        acceleration = extract_part("acc=", message=msg)
        velocity = extract_part("vel=", message=msg)

        ### if message has event append it to it
        if message and event:
            message = f"event={event}|message={message}|"

        return (receiver, identity, message,action,pitch,roll,acceleration,velocity)
    
    async def shutdown_ws_server(self):
        if hasattr(self, "server") and self.server != None:
            try:
                self.logger.info("Closing websocket server...")
                self.logger.info("Websocket server closed successfully.")
            except Exception as e:
                print("Error closing webosocket server.")
                self.logger.error("Error while closing the websocket server.")
            finally:
                os._exit(0)

    async def handle_client(self, wsclient, path=None):
        # Store client metadata
        client_info = {"identity": "unknown"}
        self.wsclients[wsclient] = client_info
        
        self.logger.info(f"Client {wsclient.remote_address} connected! Path: {path or '/'}")

        try:
            async for message in wsclient:
                print(f"Received: {message}")
                (receiver, identity, message,action,pitch,roll,acceleration,velocity) = self.extract_parts(message)
                if not action:
                    await wsclient.send("event=error|message=No action given, example action=<action>|") 
                else: 
                    if receiver:
                        self.logger.info(f"Receiver: {receiver}")
                        receiver = receiver.lower()
                    
                    # "endpoints"
                    self.logger.info(f"processing action: {action}")
                    if action == "write":
                        result = validation_service.validate_pitch_and_roll_values(pitch,roll)
                        if result:
                            await demo_control(pitch, roll, self)
                    elif action == "identify":
                        if identity:
                            client_info["identity"] = identity.lower()
                            self.logger.info(f"Updated identity for {wsclient.remote_address}: {identity}")
                        else:
                            await wsclient.send("event=error|message=No identity was given, example action=identify|identity=<identity>|") 
                    elif action == "shutdown":
                        result = await shutdown(self, wsclient)
                        
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
                        (success,receiver, msg) = validation_service.validate_message(self,receiver,message)
                        if success:
                            await receiver.send(msg)
                        else:
                            await wsclient.send(msg)
                    elif action == "clearfault":
                        try:
                            if not await self.clients.set_ieg_mode(65535) or not await self.clients.set_ieg_mode(2):
                                self.logger.error("Error clearing motors faults!")
                                await wsclient.send("event=error|message=Error clearing motors faults!|")
                                continue

                            ### success case -> inform gui and fault poller
                            succes_response = "event=faultcleared|message=Fault cleared succesfully!|"
                            fault_poller_found = False
                            await wsclient.send(succes_response) # Sending to GUI
                            for sckt, info in self.wsclients.items():
                                if info["identity"] == "fault poller":
                                    await sckt.send(succes_response)
                                    fault_poller_found = True
                                    break

                            if not fault_poller_found:
                                self.logger.error("Fault poller not found from wsclients list at server")

                        except Exception as e:
                            self.logger.error("Error clearing motors faults!")
                            await wsclient.send(f"event=error|message=Error clearing motors faults {e}!|")

        except websockets.ConnectionClosed as e:
            self.logger.error(f"Client {wsclient.remote_address} (identity: {client_info['identity']}) disconnected with code {e.code}, reason: {e.reason}")
        except Exception as e:
            self.logger.error(f"Unexpected error for client {wsclient.remote_address} (identity: {client_info['identity']}): {e}")
        finally:
            self.logger.info(f"Cleaning up for client {wsclient.remote_address} (identity: {client_info['identity']})")
            await self.cleanup_client(wsclient)

    async def cleanup_client(self, client_socket):
        # print(f"Cleaning up client: {client_socket.remote_address} (identity: {self.clients[client_socket]["identity"]})")
        if client_socket in self.wsclients:
            del self.wsclients[client_socket]
        try:
            await client_socket.close()
        except Exception as e:
            self.logger.error(f"Error closing connection for {client_socket.remote_address}: {e}")

    async def start_server(self):
        try:
            self.server = await websockets.serve(self.handle_client, "localhost", 6969, ping_timeout=None)
            self.logger.info("WebSocket serverwebsocket running on ws://localhost:6969")
        except Exception as e:
            self.logger(f"Error while launching  server{e}")

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
        print("I got here")
        await shutdown(hub)
        
if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import atexit
import os
import websockets
from ModbusClients import ModbusClients
from services.module_manager import ModuleManager
from utils.launch_params import handle_launch_params
from utils.setup_logging import setup_logging
from services.MotorApi import MotorApi
from handlers import actions
from helpers import communication_hub_helpers as helpers

class CommunicationHub:
    def __init__(self):
        self.wsclients = {}
        self.logger = setup_logging("server", "server.log")
        self.module_manager = ModuleManager(self.logger)
        self.config = handle_launch_params()
        self.clients = ModbusClients(self.config, self.logger)
        self.motor_api = MotorApi(config=self.config, logger=self.logger, modbus_clients=self.clients)
        self.is_process_done = False
        self.server = None

    async def init(self):
        try:
            await helpers.create_hearthbeat_monitor_tasks(self, self.module_manager)
            # Connect to both drivers
            connected = await self.clients.connect() 
            
            if not connected:
                self.logger.error(f"""could not form a connection to both motors,
                            Left motors ips: {self.config.SERVER_IP_LEFT}, 
                            Right motors ips: {self.config.SERVER_IP_RIGHT}, 
                            shutting down the server """)
                helpers.close_tasks()
                os._exit(1)

            self.motor_api = MotorApi(logger=self.logger, modbus_clients=self.clients)

            if not await self.motor_api.configure_motor(self.clients, self.config):
                self.clients.cleanup()
                helpers.close_tasks()
                os._exit(1)
                
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
    
    async def shutdown_server(self, wsclient=None):
        """stops and disables motors and closes sub processes"""
        self.logger.info("Shutdown request received. Cleaning up...")

        try:
            success = await self.motor_api.stop()
            if not success:
                self.logger.error("Stopping motors was not successful, will not shutdown server")
                return
        except Exception as e:
            self.logger.error("Stopping motors was not successful, will not shutdown server")
            return
        
        #########################################################################################
        #########################################################################################
        ####NOTE DO NOT REMOVE THIS LINE -IMPORTANT FOR MOTORS TO HAVE TIME TO STOP################
        await asyncio.sleep(5)
        #########################################################################################
        #########################################################################################
        #########################################################################################

        helpers.close_tasks(self)
        self.module_manager.cleanup_all()
        if self.clients is not None:
            self.clients.cleanup()

        await self.motor_api.reset_motors()
        await asyncio.sleep(20)
        
        if wsclient:
            await wsclient.send("event=shutdown|message=Server has been shutdown.|")
        
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
                (receiver, identity, message,action,pitch,roll,acceleration,velocity) = helpers.extract_parts(message)
                if not action:
                    await wsclient.send("event=error|message=No action given, example action=<action>|") 
                else: 
                    if receiver:
                        self.logger.info(f"Receiver: {receiver}")
                        receiver = receiver.lower()
                    
                    # "endpoints"
                    self.logger.info(f"processing action: {action}")
                    if action == "write":
                        result = helpers.validate_pitch_and_roll_values(pitch,roll)
                        if result:
                            await actions.demo_control(pitch, roll, self)
                    elif action == "identify":
                        if identity:
                            client_info["identity"] = identity.lower()
                            self.logger.info(f"Updated identity for {wsclient.remote_address}: {identity}")
                        else:
                            await wsclient.send("event=error|message=No identity was given, example action=identify|identity=<identity>|") 
                    elif action == "shutdown":
                        result = await self.shutdown_server(wsclient)
                        
                    elif action == "stop":
                        result = await actions.stop_motors(self)
                    elif action == "setvalues":
                        try:
                            result = helpers.validate_pitch_and_roll_values(pitch, roll)
                            if result:
                                actions.rotate(pitch,roll)
                        except ValueError as e:
                            self.logger.error(f"ValueError: {e}")
                            print(f"ValueError: {e}")
                        except Exception as e:
                            self.logger.error(f"Error while setting values: {e}")
                            print(f"Error while setting values: {e}")

                    elif action == "updatevalues":
                        result = await actions.update_input_values(self,acceleration,velocity)
                    elif action == "message":
                        (success,receiver, msg) = helpers.validate_message(self,receiver,message)
                        if success:
                            await receiver.send(msg)
                        else:
                            await wsclient.send(msg)
                    elif action == "clearfault":
                        try:
                            ### TODO muuta tämä käyttämään moottori apia
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
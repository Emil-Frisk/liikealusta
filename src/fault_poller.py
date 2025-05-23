import atexit
from time import sleep
from settings.config import Config
from utils.setup_logging import setup_logging
from ModbusClients import ModbusClients
from services.MotorApi import MotorApi
from utils.launch_params import handle_launch_params
import asyncio
from utils.utils import is_fault_critical, extract_part
from services.websocket_client import WebsocketClient
from settings.motors_config import MotorConfig

class FaultPoller():
    def __init__(self):
        self.critical_faults = {
            1: "Current in the actuator was too large.",
            128: "Board temperature is too high",
            256: "Servo motor has reached too high temperature"
        }
        self.has_faulted = False

    def on_message(self, msg):
        event = extract_part("event=", msg)
        message = extract_part("message=", msg)
        if not event:
            self.logger.error("wsclient message does not have event specified in it.")
            return
        
        if not message:
            self.logger.error("server did not specify message part")
            return
        
        if event == "error":
            self.logger.error(message)

        ### Lets fault poller continue the loop again
        if event == "faultcleared":
            self.has_faulted = False
            self.logger.info("Fault has cleared starting polling loop again")

    async def main(self):
        self.logger = setup_logging("faul_poller", "faul_poller.log")
        config = handle_launch_params()
        motor_config = MotorConfig()
        clients = ModbusClients(config=config, logger=self.logger)
        motor_api = MotorApi(logger=self.logger, modbus_clients=clients)

        connected = await clients.connect()
        if (not connected):
            return
        
        # await wsclient.connect()
        self.logger.info(f"Starting polling loop with polling time interval: {config.POLLING_TIME_INTERVAL}")
        wsclient = WebsocketClient(identity="fault poller", logger=self.logger, on_message=self.on_message)
        await wsclient.connect()

        try:
            counter = 0
            while(True):
                counter += 1
                # await asyncio.sleep(config.POLLING_TIME_INTERVAL)
                if self.has_faulted:
                    await asyncio.sleep(5)
                    continue

                ### simulated critical fault situation
                if counter == 8:
                    await wsclient.send(f"event=fault|action=message|message=CRITICAL FAULT DETECTED: {self.critical_faults[256]}|receiver=GUI|")
                    self.logger.error(f"CRITICAL FAULT DETECTED: {self.critical_faults[256]}")
                    self.has_faulted = True
                    continue

                await asyncio.sleep(1)
                ### TODO - jatka tästä inegroi käyttämään motorapia

                # motor_api.check_and_reset_tids()
                result = await motor_api.check_fault_stauts()

                if not result:
                    has_faulted = True
                else:
                    has_faulted = False

                if (has_faulted):
                    left_response, right_response = await motor_api.get_recent_fault()
                    print("Fault Poller fault status left: " + str(left_response))
                    # Check that its not a critical fault
                    (left_has_falted, right_has_faulted) = result
                    if not is_fault_critical(left_response) and not is_fault_critical(right_response):
                        ### raise reset fault bit and reset the register to 0
                        await motor_api.set_ieg_mode(motor_config.RESET_FAULT_VALUE)
                        await motor_api.set_ieg_mode(0)
                        self.logger.info("Fault cleared")
                    else:
                        if left_has_falted:
                            await wsclient.send(f"action=message|message=CRITICAL FAULT DETECTED: {self.critical_faults[left_response]}|receiver=GUI|")
                            self.logger.error(f"CRITICAL FAULT DETECTED: {self.critical_faults[left_response]}")
                        else:
                            await wsclient.send(f"action=message|message=CRITICAL FAULT DETECTED: {self.critical_faults[right_response]}|receiver=GUI|")
                            self.logger.error(f"CRITICAL FAULT DETECTED: {self.critical_faults[right_response]}")
                        self.has_faulted = True
                        
        except KeyboardInterrupt:
            self.logger.info("Polling stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in polling loop: {str(e)}")
        finally:
            clients.cleanup()
            self.logger.info("Fault poller has been closed")
            ### websocket wsclient close
            ### clean tasks

if __name__ == "__main__":
    fault_poller = FaultPoller()
    asyncio.run(fault_poller.main())
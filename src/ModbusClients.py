
from pymodbus.client import AsyncModbusTcpClient
from typing import Optional
import pymodbus.exceptions
import requests
from utils import is_nth_bit_on
import asyncio
import pymodbus
from time import sleep

class ModbusClients:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.client_left: Optional[AsyncModbusTcpClient] = None
        self.client_right: Optional[AsyncModbusTcpClient] = None
        max_retries = 5  # Maximum retry attempts
        self.retry_delay = 0.050  # Initial delay in seconds (doubles with each retry)

    async def connect(self):
        """
        Establishes connections to both Modbus clients.
        Returns True if both connections are successful, or False if either fails
        and returns None if error
        """
        try:
            self.client_left = AsyncModbusTcpClient(
                host=self.config.SERVER_IP_LEFT,
                port=self.config.SERVER_PORT
            )

            self.client_right = AsyncModbusTcpClient(
                host=self.config.SERVER_IP_RIGHT,
                port=self.config.SERVER_PORT
            )

            left_connected = False
            right_connected = False
            max_attempts = self.config.CONNECTION_TRY_COUNT
            attempt_left = 0
            attempt_right = 0

            while (not left_connected or not right_connected) and \
            (attempt_left_count < max_attempts or attempt_right_count < max_attempts):
                if not left_connected:
                    left_connected = await self.client_left.connect()
                    attempt_left_count += 1
                    if not left_connected:
                         self.logger.debug(f"Left connection attempt {attempt_left} failed")

                if not right_connected:
                    right_connected = await self.client_right.connect()
                    attempt_right_count += 1
                    if not right_connected:
                         self.logger.debug(f"Right connection attempt {attempt_right} failed")

                
            if left_connected and right_connected:
                self.logger.info("Both clients connected succesfully")
                return True
            else: 
                self.logger.warning(f"Connection failed after {max_attempts} attempts. "
                                    f"Left: {left_connected}, right: {right_connected}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error connecting to clients {str(e)}")
            return None

    def check_and_reset_tids(self):
        for client in [self.client_left, self.client_right]:
            if client and client.transaction.next_tid >= self.config.LAST_TID:
                client.transaction.next_tid = self.config.START_TID
                self.logger.debug(f"Reset TID for client")

    async def get_recent_fault(self) -> tuple[Optional[int], Optional[int]]:
        """
        Read fault registers from both clients.
        Returns tuple of (left_fault, right_fault), None if read fails
        """
        try:
            left_response = await self.client_left.read_holding_registers(
                address=self.config.RECENT_FAULT_ADDRESS,
                count=1,
                slave=self.config.SLAVE_ID
            )
            right_response = await self.client_right.read_holding_registers(
                address=self.config.RECENT_FAULT_ADDRESS,
                count=1,
                slave=self.config.SLAVE_ID
            )

            if left_response.isError() or right_response.isError():
                self.logger.error("Error reading fault register")
                return None, None
            
            return left_response.registers[0], right_response.registers[0]

        except Exception as e:
                self.logger.error(f"Exception reading fault registers: {str(e)}")
                return None, None
        
    async def check_fault_stauts(self) -> Optional[bool]:
        """
        Read drive status from both motors.
        Returns true if either one is in fault state
        otherwise false
        or None if it fails
        """
        try:
            result = False

            left_response = await self.client_left.read_holding_registers(
                address=self.config.DRIVER_STATUS_ADDRESS,
                count=1,
                slave=self.config.SLAVE_ID
            )
            right_response = await self.client_right.read_holding_registers(
                address=self.config.DRIVER_STATUS_ADDRESS,
                count=1,
                slave=self.config.SLAVE_ID
            )

            if left_response.isError() or right_response.isError():
                self.logger.error("Error reading driver status register")
                return None

            # 4th bit 2^4 indicates if motor is in the fault state
            if(is_nth_bit_on(3, left_response.registers[0]) or is_nth_bit_on(3, right_response.registers[0])):
                 result = True
            
            return result

        except Exception as e:
                self.logger.error(f"Exception checking fault status: {str(e)}")
                return None
    
    async def get_vel(self):
        """
        Gets velocity from both registers returns None if error
        """
        try:
            left_response = await  self.client_left.read_holding_registers(
                address=self.config.VFEEDBACK_VELOCITY,
                count=1,
                slave=self.config.SLAVE_ID
            )
            right_response = await self.client_right.read_holding_registers(
                address=self.config.VFEEDBACK_VELOCITY,
                count=1,
                slave=self.config.SLAVE_ID
            )

            if left_response.isError() or right_response.isError():
                self.logger.error("Error reading velocity register")
                return None, None
            
            return left_response.registers[0], right_response.registers[0]

        except Exception as e:
                self.logger.error(f"Exception reading fault registers: {str(e)}")
                return None, None

    async def stop(self):
        
            attempt_count = 0
            max_retries = max_retries

            while(max_retries >= attempt_count):
                try:
                    left_response = await self.client_left.write_register( # stop = 4
                        address=self.config.IEG_MOTION,
                        value=4,
                        slave=self.config.SLAVE_ID
                    )
                    right_response = await self.client_right.write_register(
                        address=self.config.IEG_MOTION,
                        value=4,
                        slave=self.config.SLAVE_ID
                    )

                    if left_response.isError() or right_response.isError():
                        attempt_count += 1
                        self.logger.error(f"Error stopping motor trying again i: {attempt_count}")
                        await asyncio.sleep(self.retry_delay)
                        continue

                    self.logger.info(f"Succesfully stopped both motors")        
                    return True

                except (asyncio.exceptions.TimeoutError, pymodbus.exceptions.ModbusIOException, pymodbus.exceptions.ConnectionException) as e:
                     attempt_count += 1
                     self.logger.error(f"Connection error (attempt {attempt_count}/{max_retries})")

                     if not self.client_left.connected or not self.client_right.connected:
                          await self.connect() 
                          if attempt_count < max_retries:
                            await asyncio.sleep(self.retry_delay)
                            continue
                          else:
                            self.logger.error("Max retries reached. Failed to stop motors.")
                            return False
                          
                except (Exception) as e:
                        self.logger.error(f"Something went wrong {e}")
                        return False
            
            self.logger.error("Failed to stop motors after maximum retries. Critical failure!")
            return False
        

    def cleanup(self):
        self.logger.info(f"cleanup function executed at module {self.config.MODULE_NAME}")
        if self.client_left is not None and self.client_right is not None:
            self.client_left.close()
            self.client_right.close()    
            
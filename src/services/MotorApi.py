from typing import List, Optional, Tuple, Union
from settings.motors_config import MotorConfig
from pymodbus.exceptions import ConnectionException, ModbusIOException
from utils.utils import IEG_MODE_bitmask_alternative, IEG_MODE_bitmask_default
import asyncio
from time import sleep, time
from utils.utils import is_nth_bit_on, convert_to_revs, convert_vel_rpm_revs, convert_acc_rpm_revs
import math

class MotorApi():
    def __init__(self, logger, modbus_clients,config=MotorConfig(), retry_delay = 0.2, max_retries = 10):
        self.logger = logger
        self.client_right = modbus_clients.client_right
        self.client_left = modbus_clients.client_left
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.config = config
    
    async def write(self, address, description, value=None, multiple_registers=False, values=None, different_values=False, left_val=None, right_val=None, left_vals=None, right_vals=None):
        attempt_left = 0
        attempt_right = 0
        success_right = False
        success_left = False
        max_retries = self.max_retries
        
        ### Figure out the settings based on the context
        try:
            if not multiple_registers and different_values:
                left_motor_val = left_val 
                right_motor_val = right_val 
            elif not multiple_registers and not different_values:
                left_motor_val = value
                right_motor_val = value
            elif multiple_registers and not different_values:
                left_motor_vals = values
                right_motor_vals = values
            elif multiple_registers and different_values:
                left_motor_vals = left_vals
                right_motor_vals = right_vals
            else:
                self.logger.error("Wrong settings given to register write function")
                return False
        except Exception as e:
            self.logger.error(f"Error while trying to setup settings for register write operation: {e}")
        
        if not multiple_registers:
            try:
                while max_retries > attempt_left and max_retries > attempt_right:
                    if not success_right:
                        response_right = await self.client_right.write_register(
                            address=address,
                            value=right_motor_val,
                            slave=self.config.SLAVE_ID)
                    if not success_left:
                        response_left = await self.client_left.write_register(
                            address=address,
                            value=left_motor_val,
                            slave=self.config.SLAVE_ID)

                    if response_left.isError():
                        attempt_left += 1
                        self.logger.error(f"Failed to {description} on left. Attempt {attempt_left}")
                    else:
                        success_left = True

                    if response_right.isError():
                        attempt_right += 1
                        self.logger.error(f"Failed to {description} on right motor. Attempt {attempt_right}")
                    else:
                        success_right = True
                    
                    if success_left and success_right:
                        self.logger.info(f"succesfully {description} on both motors!")
                        return True
                    
                    # Delay between retries
                    await asyncio.sleep(self.retry_delay)
                
                if not success_left or not success_right:
                    self.logger.error(f"Failed to {description} on both motors. Left: {success_left} | Right: {success_right}")
                    return False
            except Exception as e:
                self.logger.error(f"Unexpected error while {description}: {str(e)}")
                return False
        else:
            try:
                while max_retries > attempt_left and max_retries > attempt_right:
                    if not success_right:
                        response_right = await self.client_right.write_registers(
                            address=address,
                            values=right_motor_vals,
                            slave=self.config.SLAVE_ID)
                    if not success_left:
                        response_left = await self.client_left.write_registers(
                            address=address,
                            values=left_motor_vals,
                            slave=self.config.SLAVE_ID)

                    if response_left.isError():
                        attempt_left += 1
                        self.logger.error(f"Failed to {description} on left. Attempt {attempt_left}")
                    else:
                        success_left = True

                    if response_right.isError():
                        attempt_right += 1
                        self.logger.error(f"Failed to {description} on right motor. Attempt {attempt_right}")
                    else:
                        success_right = True
                    
                    if success_left and success_right:
                        self.logger.info(f"succesfully {description} on both motors!")
                        return True
                    
                    # Delay between retries
                    await asyncio.sleep(self.retry_delay)
                
                if not success_left or not success_right:
                    self.logger.error(f"Failed to {description} on both motors. Left: {success_left} | Right: {success_right}")
                    return False
            except Exception as e:
                self.logger.error(f"Unexpected error while {description}: {str(e)}")
                return False
    
    async def read(self, address, description, count=2, log=True):
        try:
            attempt_left = 0
            attempt_right = 0
            success_left = False
            success_right = False
            max_retries = self.max_retries

            while max_retries > attempt_left and max_retries > attempt_right:
                # Write to left motor if not yet successful
                if not success_left:
                    response_left = await self.client_left.read_holding_registers(
                        address=address,
                        count=count,
                        slave=self.config.SLAVE_ID
                    )
                    if response_left.isError():
                        attempt_left += 1
                        self.logger.error(f"Failed to {description} on left motor. Attempt {attempt_left}/{max_retries}")
                    else:
                        success_left = True
                        self.logger.info(f"Successfully {description} on left motor")

                # Read from right motor if not yet successful
                if not success_right:
                    response_right = await self.client_right.read_holding_registers(
                        address=address,
                        count=count,
                        slave=self.config.SLAVE_ID
                    )
                    if response_right.isError():
                        attempt_right += 1
                        self.logger.error(f"Failed to {description} on right motor. Attempt {attempt_right}/{max_retries}")
                    else:
                        success_right = True
                        self.logger.info(f"Successfully {description} on right motor")

                # Break if both are successful
                if success_left and success_right:
                    break

                # Delay between retries
                await asyncio.sleep(self.retry_delay)

            if not success_left or not success_right:
                self.logger.error(f"Failed to {description} on both motors. Left: {success_left}, Right: {success_right}")
                return False

            if log:
                self.logger.info(f"Successfully {description} on both motors")
            return (response_left, response_right)

        except Exception as e:
            self.logger.error(f"Unexpected error while reading motor REVS: {str(e)}")
            return False
    
    async def reset_motors(self):
        """ 
        Removes all temporary settings from both motors
        and goes back to default ones
        """
        return await self.write(address=self.config.SYSTEM_COMMAND, value=self.config.RESTART_VALUE, description="force a software power-on restart of the drive")

    async def get_recent_fault(self) -> tuple[Optional[int], Optional[int]]:
        """
        Read fault registers from both clients.
        Returns tuple of (left_fault, right_fault), None if read fails
        """
        return await self.read(address=self.config.RECENT_FAULT_ADDRESS, description="read fault register", count=1)
        
    async def fault_reset(self, mode = "default"):
        # Makes sure bits can be only valid bits that we want to control
        # no matter what you give as a input
        return await self.write(value=IEG_MODE_bitmask_default(65535), address=self.config.IEG_MODE, description="reset faults")

    async def check_fault_stauts(self, log=True) -> Optional[bool]:
        """
        Read drive status from both motors.
        Returns true if either one is in fault state
        otherwise false
        or None if it fails
        """
        return await self.read(log=log, address=self.config.OEG_STATUS, description="read driver status",count=1)
    
    async def get_vel(self):
        """
        Gets VEL32_HIGH register for both motors
        """
        return await self.read(address=self.config.VFEEDBACK_VELOCITY,description="read velocity register", count=1)
   
    async def stop(self):
        """
        Attempts to stop both motors by writing to the IEG_MOTION register.
        Returns True if successful, False if failed after retries.
        """
        return await self.write(address=self.config.IEG_MOTION, value=self.config.STOP_VALUE, description="Stop motors")

    async def home(self):
        try:
            ### Reset IEG_MOTION bit to 0 so we can trigger rising edge with our home command
            if not await self.write(address=self.config.IEG_MOTION, value=0, description="reset IEG_MOTION to 0"):
                return False
                
            ### Initiate homing command
            if not await self.write(value=self.config.HOME_VALUE, address=self.config.IEG_MOTION, description="initiate homing command"): 
                return False
            
            ### homing order was success for both motos make a poller coroutine to poll when the homing is done.
            #Checks if both actuators are homed or not. Returns True when homed.
            homing_max_duration = 30
            start_time = time()
            elapsed_time = 0
            while elapsed_time <= homing_max_duration:
                response = await self.read(address=self.config.OEG_STATUS, description="Read OEG_STATUS",count=1)
                if not response:
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                (OEG_STATUS_right, OEG_STATUS_left) = response
                
                ishomed_right = is_nth_bit_on(1, OEG_STATUS_right.registers[0])
                ishomed_left = is_nth_bit_on(1, OEG_STATUS_left.registers[0])

                # Success
                if ishomed_right and ishomed_left:
                    self.logger.info(f"Both motors homes successfully:")
                    await self.write(address=self.config.IEG_MOTION, value=0, description="reset IEG_MOTION to 0")
                    return True
                
                await asyncio.sleep(1)
                elapsed_time = time() - start_time
            
            self.logger.error(f"Failed to home both motors within the time limit of: {homing_max_duration}")
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error while homing motors: {e}")
            return False
    
    async def set_analog_pos_max(self, decimal: int, whole: int) -> bool:
        """
        Sets the analog position maximum for both motors.
        Args:
            decimal (int): The decimal part of the position limit.
            whole (int): The whole number part of the position limit.
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        values = [decimal, whole]
        return await self.write(multiple_registers=True, values=values, description="set analog positition max", address=self.config.ANALOG_POSITION_MAXIMUM)
                
    async def set_analog_pos_min(self, decimal: int, whole: int) -> bool:
        """
        Sets the analog position minium for both motors.
        Args:
            decimal (int): The decimal part of the position limit.
            whole (int): The whole number part of the position limit.
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        values = [decimal, whole]
        return await self.write(multiple_registers=True, values=values, description="set analog position min", address=self.config.ANALOG_POSITION_MINIMUM)

    async def set_analog_vel_max(self, decimal: int, whole: int) -> bool:
        """
        Sets the analog velocity maxium for both motors.
        Args:
            decimal (int): The decimal part of the velocity limit.
            whole (int): The whole number part of the velocity limit.
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        values = [decimal, whole]
        return await self.write(multiple_registers=True, values=values, description="set analog velocity max", address=self.config.ANALOG_VEL_MAXIMUM)
    
    async def set_analog_acc_max(self, decimal: int, whole: int) -> bool:
        """
        Sets the analog acceleration maxium for both motors.
        Args:
            decimal (int): The decimal part of the acceleration limit.
            whole (int): The whole number part of the acceleration limit.
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        values = [decimal, whole]
        return await self.write(multiple_registers=True, values=values, description="set analog acceleration maxium", address=self.config.ANALOG_ACCELERATION_MAXIMUM)

    async def set_analog_input_channel(self, value: int) -> bool:
        """
        Sets the analog input channel for both motors.
        Args:
            value (int): The value for the analog input channel.
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        return await self.write(value=value, address=self.config.ANALOG_INPUT_CHANNEL, description="set analog input channel")
        
    async def get_current_revs(self) ->  Union[Tuple[List[int], List[int]], bool]:
        """
        Gets the current REVS for both motors
        Returns:
             A tuple of (response_left, response_right), where each response is a list of two integers:
            - response_left: [decimal_part, whole_part] for the left motor
            - response_right: [decimal_part, whole_part] for the right motor
            Returns False if the operation is not successful.
        """
        return await self.read(address=self.config.PFEEDBACK_POSITION, description="read current REVS", count=2)
    
    async def set_analog_modbus_cntrl(self, values: Tuple[int, int]) -> bool:
        """
        Sets the analog input Modbus control value for both motors,
        where 0 makes the motor go to the analog_pos_min position
        and 10,000 makes the motor go to the analog_pos_max position.
        Args:
            values: A tuple of (value_left, value_right) where each value is an integer
                    between 0 and 10,000 representing the control value for the left and right motors.
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        value_left, value_right = values
        return await self.write(different_values=True, right_val=value_right, left_val=value_left, description="Set analog modbus control value", address=self.config.ANALOG_MODBUS_CNTRL)
    
    async def wait_for_motors_to_stop(self) -> bool:
        """ Polls for motors to stop returns True or False"""
        ### TODO - figure out velocity feedback register
        try:
            waiting_duration = 30
            start_time = time()
            elapsed_time = 0
            while elapsed_time <= waiting_duration:
                response_left, response_right = await self.get_vel()
                if response_left == None or response_right == None:
                    await asyncio.sleep(0.2)
                    elapsed_time = time() - start_time
                    self.logger.error(f"Failed to get current motor velocity:")
                    continue
                
                ### get the whole number
                velocity_left = response_left >> 8
                velocity_right = response_right >> 8

                # Success
                if velocity_left == 0 and velocity_right == 0:
                    self.logger.info(f"Both motors have successfully stopped:")
                    await asyncio.sleep(0.5) ### add some safety buffer 
                    return True
                
                await asyncio.sleep(0.2)
                elapsed_time = time() - start_time
            
            self.logger.error(f"Waiting for motors to stop was not successful within the time limit of: {waiting_duration}")
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error while waiting for motors to stop: {e}")
            return False

    async def set_host_command_mode(self, value: int) -> bool:
        """
        Sets both of the motors host command mode to value
        Args:
            value: 
            OPMODE MAP
                0: disabled
                1: digital inputs
                2: analog position
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        return await self.write(address=self.config.COMMAND_MODE, value=value, description="set host command mode")
        
    async def set_ieg_mode(self, value: int) -> bool:
        """
        Sets IEG_MODE bits
        !!! IMPORTANT NOTE !!! 
        DO NOT EVER ACTIVATE ALL BITS IT WILL DEFINE NEW HOME AND THE WHOLE SYSTEM
        WILL BRAKE, IT WILL ALSO DISABLE THE MOTORS BREAKS MAKE SURE TO USE
        BIT MAKS DEFINED IN THE UTILS (IEG_MODE_bitmask_default) and (IEG_MODE_bitmask_alternative)
        THESE BITMASKS WILL MAKE SURE DANGEROUS BITS WILL NEVER BE ON EVEN IF YOU USE MAX UINT32 VALUE
        Args:
            value: 
            bit map
                0: enable momentary
                1: enable maintained
                7: alt mode
                15: reset fault
        Returns:
            bool: True if successful for both motors, False otherwise.
        """
        return await self.write(description="set IEG_MODE", value=IEG_MODE_bitmask_default(value), address=self.config.IEG_MODE)
        
    async def get_modbuscntrl_val(self):
        """
        Gets the current revolutions of both motors and calculates with linear interpolation
        the percentile where they are in the current max_rev - min_rev range.
        After that we multiply it with the maxium modbuscntrl val (10k)
        """
        result = await self.get_current_revs()
        
        if result is False:
            return False

        try:
            pfeedback_client_left, pfeedback_client_right = result

            revs_left = convert_to_revs(pfeedback_client_left)
            revs_right = convert_to_revs(pfeedback_client_right)

            ## Percentile = x - pos_min / (pos_max - pos_min)
            POS_MIN_REVS = self.config.POS_MIN_REVS
            POS_MAX_REVS = self.config.POS_MAX_REVS
            modbus_percentile_left = (revs_left - POS_MIN_REVS) / (POS_MAX_REVS - POS_MIN_REVS)
            modbus_percentile_right = (revs_right - POS_MIN_REVS) / (POS_MAX_REVS - POS_MIN_REVS)
            modbus_percentile_left = max(0, min(modbus_percentile_left, 1))
            modbus_percentile_right = max(0, min(modbus_percentile_right, 1))

            position_client_left = math.floor(modbus_percentile_left * self.config.MODBUSCTRL_MAX)
            position_client_right = math.floor(modbus_percentile_right * self.config.MODBUSCTRL_MAX)
            return position_client_left, position_client_right
        except Exception as e:
            self.logger.error(f"Unexpected error while converting to revs: {e}")
            return False
        
    async def initialize_motor(self):
        """ Tries to initialize the motors with initial values returns true if succesful """
        await self.set_host_command_mode(0)
        await self.set_ieg_mode(self.config.RESET_FAULT_VALUE)
        homed = await self.home()

        if homed: 
            ## Prepare motor parameters for operation
            ### MAX POSITION LIMITS FOR BOTH MOTORS | 147 mm
            if not await self.set_analog_pos_max(61406, 28):
                return False

            ### MIN POSITION LIMITS FOR BOTH MOTORS || 2 mm
            if not await self.set_analog_pos_min(25801, 0):
                return False

            ### Velocity whole number is in 8.8 where decimal is in little endian format,
            ### meaning smaller bits come first, so 1 rev would be 2^8
            
            ### TODO - move convert vel rmp revs and acc to motorapi helpers instead
            (velocity_whole, velocity_decimal) = convert_vel_rpm_revs(self.config.VEL)
            if not await self.set_analog_vel_max(velocity_decimal, velocity_whole):
                return False

            ### UACC32 whole number split in 12.4 format
            (acc_whole, acc_decimal) = convert_acc_rpm_revs(self.config.ACC)
            if not await self.set_analog_acc_max(acc_decimal, acc_whole):
                return False

            ## Analog input channel set to use modbusctrl (2)
            if not await self.set_analog_input_channel(self.config.ANALOG_MODBUS_CNTRL_VALUE):
                return False

            response = await self.get_modbuscntrl_val()
            if not response:
                return False
            (position_client_left, position_client_right) = response

            # modbus cntrl 0-10k
            if not await self.set_analog_modbus_cntrl((position_client_left, position_client_right)):
                return False

            # # Finally - Ready for operation
            if not await self.set_host_command_mode(self.config.ANALOG_POSITION_MODE):
                return False

            # Enable motors
            if not await self.set_ieg_mode(self.config.ENABLE_MAINTAINED_VALUE):
                return False
            
            return True
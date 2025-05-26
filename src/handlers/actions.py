
from services.validation_service import validate_update_values
from utils.utils import convert_acc_rpm_revs, convert_to_revs, convert_vel_rpm_revs
from helpers import communication_hub_helpers as helpers
import math

async def set_values(self, pitch, roll, wsclient):
    try:
        result = helpers.validate_pitch_and_roll_values(pitch, roll)
        if result:
            await self.motor_api.rotate(pitch,roll)
    except ValueError as e:
        self.logger.error(f"pitch and roll were not numbers: {e}")
        await wsclient.send("event=error|message=pitch and roll were not numbers. Please give integers|")
    except Exception as e:
        self.logger.error(f"Error while setting values: {e}")
        await wsclient.send("event=error|message=Something went wrong check logs server.log|")

async def clear_fault(self, wsclient):
    try:
        if not await self.motor_api.set_ieg_mode(self.motor_config.RESET_FAULT_VALUE):
            self.logger.error("Error clearing motors faults!")
            await wsclient.send("event=error|message=Error clearing motors faults!|")
        else:
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
    except:
        self.logger.error("Error clearing motors faults!")
        await wsclient.send(f"event=error|message=Error clearing motors faults {e}!|")

async def message(self, wsclient, message):
    try:
        (success,receiver, msg) = helpers.validate_message(self,receiver,message)
        if success:
            await receiver.send(msg)
        else:
            await wsclient.send(msg)
    except Exception as e:
        self.logger.error(f"Something went wrong while trying to send a message {e}")

async def demo_control(self, pitch, roll):
    MODBUSCTRL_MAX = self.config
    if (pitch == "+"): # forward
        response = await self.motor_api.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl ")

        (position_client_left, position_client_right) = response
        position_client_left = math.floor(position_client_left + (MODBUSCTRL_MAX * 0.15)) 
        position_client_right = math.floor(position_client_right + (MODBUSCTRL_MAX* 0.15)) 

        position_client_right = min(MODBUSCTRL_MAX, position_client_right)
        position_client_left = min(MODBUSCTRL_MAX, position_client_left)

        await self.motor_api.set_analog_modbus_cntrl((position_client_left, position_client_right))
    elif (pitch == "-"): #backward
        response = await self.motor_api.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl val")
        (position_client_left, position_client_right) = response

        position_client_left = math.floor(position_client_left - (MODBUSCTRL_MAX* 0.15)) 
        position_client_right = math.floor(position_client_right - (MODBUSCTRL_MAX* 0.15)) 

        position_client_right = max(0, position_client_right)
        position_client_left = max(0, position_client_left)

        await self.motor_api.set_analog_modbus_cntrl((position_client_left, position_client_right))
    elif (roll == "-"):# left
        response = await self.motor_api.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl val")
        (position_client_left, position_client_right) = response
        position_client_left = math.floor(position_client_left - (MODBUSCTRL_MAX* 0.08)) 
        position_client_right = math.floor(position_client_right + (MODBUSCTRL_MAX* 0.08)) 

        position_client_right = min(MODBUSCTRL_MAX, position_client_right)
        position_client_left = max(0, position_client_left)
        
        await self.motor_api.set_analog_modbus_cntrl((position_client_left, position_client_right))
    elif (roll == "+"):
        response = await self.motor_api.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl val")
        (position_client_left, position_client_right) = response

        position_client_left = math.floor(position_client_left + (MODBUSCTRL_MAX* 0.20)) 
        position_client_right = math.floor(position_client_right - (MODBUSCTRL_MAX* 0.20)) 

        position_client_left = min(MODBUSCTRL_MAX, position_client_left)
        position_client_right = max(0, position_client_right)

        await self.motor_api.set_analog_modbus_cntrl((position_client_left, position_client_right))
    else:
        self.logger.error("Wrong parameter use direction (l | r)")

async def stop_motors(self):
    try:
        success = await self.motor_api.stop()
        if not success:
            pass # do something crazy :O
    except Exception as e:
        self.logger.error("Failed to stop motors?") # Mitäs sitten :D
    return {"status": "success"}

async def update_input_values(self,acceleration,velocity):
    try:
        values = {acceleration: acceleration, velocity: velocity}
        if not validate_update_values(values):
            raise ValueError()
        
        if 'velocity' in values:
            (velocity_whole, velocity_decimal) = convert_vel_rpm_revs(values["velocity"])
            if not await self.motor_api.set_analog_vel_max(velocity_decimal, velocity_whole):
                print("Velocity not uptaded successfully")
        if 'acceleration' in values:
            (acc_decimal, acc_whole) = convert_acc_rpm_revs(values["acceleration"])
            if not await self.motor_api.set_analog_acc_max(acc_decimal, acc_whole):
                self.logger.error("Acceleration not uptaded successfully")

        return {"status":"success"}
    except ValueError as e:
        return {"status": "error", "message": "Velocity and Acceleration has to be positive integers"}
    except Exception as e:
        self.logger.error(f"Error while updating motors values: {e}")
        return {"status": "error", "message": "Unexpected error while trying to update motors values"}
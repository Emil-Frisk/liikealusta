
from services.validation_service import validate_update_values
from utils.utils import convert_acc_rpm_revs, convert_to_revs, convert_vel_rpm_revs
import math

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

async def rotate(self, pitch_value, roll_value):
    try:
        # Tarkistetaan että annettu pitch -kulma on välillä -8.5 <-> 8.5
        pitch_value = max(-8.5, min(pitch_value, 8.5))

        # Laske MaxRoll pitch -kulman avulla
        MaxRoll = 0.002964 * pitch_value**4 + 0.000939 * pitch_value**3 - 0.424523 * pitch_value**2 - 0.05936 * pitch_value + 15.2481

        # Laske MinRoll MaxRoll -arvon avulla
        MinRoll = -1 * MaxRoll

        # Verrataan Roll -kulmaa MaxRoll ja MinRoll -arvoihin
        roll_value = max(MinRoll, min(roll_value, MaxRoll))

        # Valitse käytettävä Roll -lauseke
        dif = roll_value - 0
        if dif == 0:
        # if roll_value == 0:
            Relaatio = 1
        elif pitch_value < -2:
            Relaatio = 0.984723 * (1.5144)**roll_value
        elif pitch_value > 2:
            Relaatio = 0.999843 * (1.08302)**roll_value
        else:    
            Relaatio = 1.0126 * (1.22807)**roll_value

        # Laske keskipituus
        Keskipituus = 0.027212 * (pitch_value)**2 + 8.73029 * pitch_value + 73.9818

        # Määritä servomoottorien pituudet

        # Vasen servomoottori kierroksina
        VasenServo = ((2 * Keskipituus * Relaatio) / (1 + Relaatio)) / (0.2 * 25.4)

        # Oikea servomoottori kierroksina
        OikeaServo = ((2 * Keskipituus) / (1 + Relaatio)) / (0.2 * 25.4)

        ## Percentile = x - pos_min / (pos_max - pos_min)
        POS_MIN_REVS = 0.393698024
        POS_MAX_REVS = 28.937007874015748031496062992126
        modbus_percentile_left = (VasenServo - POS_MIN_REVS) / (POS_MAX_REVS - POS_MIN_REVS)
        modbus_percentile_right = (OikeaServo - POS_MIN_REVS) / (POS_MAX_REVS - POS_MIN_REVS)
        modbus_percentile_left = max(0, min(modbus_percentile_left, 1))
        modbus_percentile_right = max(0, min(modbus_percentile_right, 1))

        position_client_left = math.floor(modbus_percentile_left * self.app_config.MODBUSCTRL_MAX)
        position_client_right = math.floor(modbus_percentile_right * self.app_config.MODBUSCTRL_MAX)

        await self.motor_api.set_analog_modbus_cntrl((position_client_left, position_client_right))
    except Exception as e:
            self.logger.error("Error with pitch and roll calculations!")
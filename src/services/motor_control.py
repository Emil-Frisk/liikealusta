import math

async def demo_control(pitch, roll, self):
    MODBUSCTRL_MAX = self.app_config.MODBUSCTRL_MAX
    if (pitch == "+"): # forward
        response = await self.clients.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl ")
        (position_client_left, position_client_right) = response

        position_client_left = math.floor(position_client_left + (MODBUSCTRL_MAX * 0.15)) 
        position_client_right = math.floor(position_client_right + (MODBUSCTRL_MAX* 0.15)) 

        position_client_right = min(MODBUSCTRL_MAX, position_client_right)
        position_client_left = min(MODBUSCTRL_MAX, position_client_left)

        await self.clients.client_right.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_right, slave=self.app_config.SLAVE_ID)
        await self.clients.client_left.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_left, slave=self.app_config.SLAVE_ID)

    elif (pitch == "-"): #backward
        response = await self.clients.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl val")
        (position_client_left, position_client_right) = response

        position_client_left = math.floor(position_client_left - (MODBUSCTRL_MAX* 0.15)) 
        position_client_right = math.floor(position_client_right - (MODBUSCTRL_MAX* 0.15)) 

        position_client_right = max(0, position_client_right)
        position_client_left = max(0, position_client_left)

        await self.clients.client_right.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_right, slave=self.app_config.SLAVE_ID)
        await self.clients.client_left.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_left, slave=self.app_config.SLAVE_ID)
    elif (roll == "-"):# left
        response = await self.clients.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl val")
        (position_client_left, position_client_right) = response
        position_client_left = math.floor(position_client_left - (MODBUSCTRL_MAX* 0.08)) 
        position_client_right = math.floor(position_client_right + (MODBUSCTRL_MAX* 0.08)) 

        position_client_right = min(MODBUSCTRL_MAX, position_client_right)
        position_client_left = max(0, position_client_left)

        await self.clients.client_right.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_right, slave=self.app_config.SLAVE_ID)
        await self.clients.client_left.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_left, slave=self.app_config.SLAVE_ID)
    elif (roll == "+"):
        response = await self.clients.get_modbuscntrl_val()
        if not response:
            self.logger.error("Failed to get modbuscntrl val")
        (position_client_left, position_client_right) = response

        position_client_left = math.floor(position_client_left + (MODBUSCTRL_MAX* 0.20)) 
        position_client_right = math.floor(position_client_right - (MODBUSCTRL_MAX* 0.20)) 

        position_client_left = min(MODBUSCTRL_MAX, position_client_left)
        position_client_right = max(0, position_client_right)

        await self.clients.client_right.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_right, slave=self.app_config.SLAVE_ID)
        await self.clients.client_left.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_left, slave=self.app_config.SLAVE_ID)
    else:
        self.logger.error("Wrong parameter use direction (l | r)")

async def rotate(pitch_value, roll_value, self):
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

        await self.clients.client_right.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_right, slave=self.app_config.SLAVE_ID)
        await self.clients.client_left.write_register(address=self.app_config.ANALOG_MODBUS_CNTRL, value=position_client_left, slave=self.app_config.SLAVE_ID)
        
    except Exception as e:
            self.logger.error("Error with pitch and roll calculations!")
    
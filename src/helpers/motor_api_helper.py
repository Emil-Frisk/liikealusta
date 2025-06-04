import math

def get_register_values(data):
    left_data, right_data = data
    left_vals = []
    right_vals = []
    for register in left_data.registers:
        left_vals.append(register)

    for register in right_data.registers:
        right_vals.append(register)
        
    return (left_vals, right_vals)
    

def calculate_motor_modbuscntrl_vals(self, pitch_value, roll_value):
        try:
            roll_value = max(-15, min(roll_value, 15))
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

            position_client_left = math.floor(modbus_percentile_left * self.config.MODBUSCTRL_MAX)
            position_client_right = math.floor(modbus_percentile_right * self.config.MODBUSCTRL_MAX)

            return position_client_left, position_client_right
        except Exception as e:
            self.logger.error(f"soemthing went wrong in trying to calculate modbuscntrl vals")
            return False

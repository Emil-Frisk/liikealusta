import math
from utils.utils import unnormalize_decimal

def get_register_values(data):
    left_data, right_data = data
    left_vals = []
    right_vals = []
    for register in left_data.registers:
        left_vals.append(register)

    for register in right_data.registers:
        right_vals.append(register)
        
    return (left_vals, right_vals)
    

def calculate_target_revs(self, pitch_value, roll_value):
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

            ### unnormalize decimal values between 0-65535
            left_decimal, left_whole = math.modf(VasenServo)
            left_decimal = min(self.config.MAX_POS32_DECIMAL, left_decimal)
            left_pos_low = unnormalize_decimal(left_decimal, 16)

            right_decimal, right_whole = math.modf(OikeaServo)
            right_decimal = min(self.config.MAX_POS32_DECIMAL, right_decimal)
            right_pos_low = unnormalize_decimal(right_decimal, 16)

            ### Clamp position to a safe range
            ### min 2mm
            if left_whole <= self.config.MIN_POS_WHOLE: 
                 left_pos_low = max(self.config.MIN_POS_DECIMAL, left_pos_low)
                 left_whole = self.config.MIN_POS_WHOLE
            
            ### min 2mm
            if right_whole <= self.config.MIN_POS_WHOLE: 
                 right_pos_low = max(self.config.MIN_POS_DECIMAL, right_pos_low)
                 right_whole = self.config.MIN_POS_WHOLE

            #### MAX 147 mm
            if left_whole >= self.config.MAX_POS_WHOLE:
                 left_pos_low = min(self.config.MAX_POS_DECIMAL, left_pos_low)
                 left_whole = self.config.MAX_POS_WHOLE

            #### MAX 147 mm
            if right_whole >= self.config.MAX_POS_WHOLE:
                 right_pos_low = min(self.config.MAX_POS_DECIMAL, right_pos_low)
                 right_whole = self.config.MAX_POS_WHOLE

            return ((left_decimal, left_whole), (right_decimal, right_whole))
        except Exception as e:
            self.logger.error(f"soemthing went wrong in trying to calculate modbuscntrl vals")
            return False
        


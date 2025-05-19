import time
import random
import math
import numba

# Save the start time before the loop

@numba.jit(nopython=True, fastmath=True)
def jit_functio(random_pitch, random_roll):

    # Tarkistetaan että annettu pitch -kulma on välillä -8 <-> 8
    Pitch = max(-8.5, min(random_pitch, 8.5))

    # Laske MaxRoll pitch -kulman avulla
    MaxRoll = 0.002964 * Pitch**4 + 0.000939 * Pitch**3 - 0.424523 * Pitch**2 - 0.05936 * Pitch + 15.2481

    # Laske MinRoll MaxRoll -arvon avulla
    MinRoll = -1 * MaxRoll

    # Verrataan Roll -kulmaa MaxRoll ja MinRoll -arvoihin
    Roll = max(MinRoll, min(random_roll, MaxRoll))

    # Valitse käytettävä Roll -lauseke
    if Roll == 0:
        Relaatio = 1
    elif Pitch < -2:
        Relaatio = 0.984723 * (1.5144)**Roll
    elif Pitch > 2:
        Relaatio = 0.999843 * (1.08302)**Roll
    else:    
        Relaatio = 1.0126 * (1.22807)**Roll

    # Laske keskipituus
    Keskipituus = 0.027212 * (Pitch)**2 + 8.73029 * Pitch + 73.9818

    # Määritä servomoottorien pituudet

    # Vasen servomoottori
    VasenServo = (2 * Keskipituus * Relaatio) / (1 + Relaatio)

    # Oikea moottori
    OikeaServo = (2 * Keskipituus) / (1 + Relaatio)

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

    position_client_left = math.floor(modbus_percentile_left * 10000)
    position_client_right = math.floor(modbus_percentile_right * 10000)


# Loop 1000 times

iteration_count = 1000000

for i in range(10):
    jit_functio(2, 3)

start_time = time.time()
for i in range(iteration_count):
    # You can add any code here that you want to measure
    random_pitch = random.uniform(-9.0, 9.0)
    random_roll = random.uniform(-16.0, 16)
    jit_functio(random_pitch=random_pitch, random_roll=random_roll)

# Save the end time after the loop
end_time = time.time()

# Calculate the time taken (difference between end and start times)
time_taken = end_time - start_time

# Print the time taken to complete the loop
print(f"Time taken for {iteration_count} iterations: {time_taken} seconds")

start_time = time.time()
### JIT - import numpa
for i in range(iteration_count):
    # You can add any code here that you want to measure
    random_pitch = random.uniform(-9.0, 9.0)
    random_roll = random.uniform(-16.0, 16)
    # Tarkistetaan että annettu pitch -kulma on välillä -8 <-> 8
    Pitch = max(-8.5, min(random_pitch, 8.5))

    # Laske MaxRoll pitch -kulman avulla
    MaxRoll = 0.002964 * Pitch**4 + 0.000939 * Pitch**3 - 0.424523 * Pitch**2 - 0.05936 * Pitch + 15.2481

    # Laske MinRoll MaxRoll -arvon avulla
    MinRoll = -1 * MaxRoll

    # Verrataan Roll -kulmaa MaxRoll ja MinRoll -arvoihin
    Roll = max(MinRoll, min(random_roll, MaxRoll))

    # Valitse käytettävä Roll -lauseke
    if Roll == 0:
        Relaatio = 1
    elif Pitch < -2:
        Relaatio = 0.984723 * (1.5144)**Roll
    elif Pitch > 2:
        Relaatio = 0.999843 * (1.08302)**Roll
    else:    
        Relaatio = 1.0126 * (1.22807)**Roll

    # Laske keskipituus
    Keskipituus = 0.027212 * (Pitch)**2 + 8.73029 * Pitch + 73.9818

    # Määritä servomoottorien pituudet

    # Vasen servomoottori
    VasenServo = (2 * Keskipituus * Relaatio) / (1 + Relaatio)

    # Oikea moottori
    OikeaServo = (2 * Keskipituus) / (1 + Relaatio)

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

    position_client_left = math.floor(modbus_percentile_left * 10000)
    position_client_right = math.floor(modbus_percentile_right * 10000)

end_time = time.time()

time_taken = end_time - start_time
print(f"Time taken for {iteration_count} iterations: {time_taken} seconds")
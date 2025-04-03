import math
import numpy as np

Pitch = 5.0
Roll = 10.0
MaxRoll = 0.0
MinRoll = -0.0

#print("Pitch is:", Pitch,)
#print("Roll is:", Roll)
#print("MaxRoll is:", MaxRoll)
#print("MinRoll is:", MinRoll)

# Laske MaxRoll pitch -kulman avulla
MaxRoll = 0.003312 * Pitch**4 + 0.001289 * Pitch**3 - 0.452678 * Pitch**2 - 0.075458 * Pitch + 15.6906

# Laske MinRoll MaxRoll -arvon avulla
MinRoll = -1 * MaxRoll

#print("MaxRoll is:", MaxRoll)
#print("MinRoll is:", MinRoll)

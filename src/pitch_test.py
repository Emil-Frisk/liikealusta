import math
import numpy as np

Pitch = -3.0
Roll = 9.0
MaxRoll = 0.0
MinRoll = -0.0

#print("Pitch is:", Pitch,)
#print("Roll is:", Roll)
#print("MaxRoll is:", MaxRoll)
#print("MinRoll is:", MinRoll)

# Laske MaxRoll pitch -kulman avulla
MaxRoll = 0.002964 * Pitch**4 + 0.000939 * Pitch**3 - 0.424523 * Pitch**2 - 0.05936 * Pitch + 15.2481

# Laske MinRoll MaxRoll -arvon avulla
MinRoll = -1 * MaxRoll

print("MaxRoll is:", MaxRoll)
print("MinRoll is:", MinRoll)

# Verrataan Roll -kulmaa MaxRoll ja MinRoll -arvoihin
if Roll > MaxRoll:
    Roll = MaxRoll
elif Roll < MinRoll:
    Roll = MinRoll

#print("Pitch is:", Pitch,)
print("Roll is:", Roll)
#print("MaxRoll is:", MaxRoll)
#print("MinRoll is:", MinRoll)



# Valitse käytettävä Roll -lauseke

if Pitch < -2:
    Relaatio = 0.984723 * (1.5144)**Roll
elif Pitch > 2:
    Relaatio = 0.999843 * (1.08302)**Roll
else:
    Relaatio = 1.0126 * (1.22807)**Roll

#print("Relaatio on:", Relaatio)


# Laske keskipituus

Keskipituus = 0.027212 * (Pitch)**2 + 8.73029 * Pitch + 73.9818

#print("Keskipituus on:", Keskipituus)

# Määritä servomoottorien pituudet

# Vasen servomoottori
VasenServo = (2 * Keskipituus * Relaatio) / (1 + Relaatio)

# Oikea moottori
OikeaServo = (2 * Keskipituus) / (1 + Relaatio)

print("Vasemman servon pituus:", VasenServo, "mm")
print("Oikean servon pituus:", OikeaServo, "mm")
print()
print("Vasemman servon pituus:", VasenServo / (0.2 * 25.4))
print("Oikean servon pituus:", OikeaServo / (0.2 * 25.4))
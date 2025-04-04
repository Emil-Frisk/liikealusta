import math

# Saadaan syötteinä Roll ja Pitch -kulmat
#Pitch = -2.5
#Roll = 10.0
User_Imput = input("Anna pitch -kulma: ")
Pitch = float(User_Imput)
User_Imput = input("Anna roll -kulma: ")
Roll = float(User_Imput)

# Tarkistetaan että annettu pitch -kulma on välillä -8 <-> 8
Pitch = max(-8, min(Pitch, 8))

# Laske MaxRoll pitch -kulman avulla
MaxRoll = 0.002964 * Pitch**4 + 0.000939 * Pitch**3 - 0.424523 * Pitch**2 - 0.05936 * Pitch + 15.2481

# Laske MinRoll MaxRoll -arvon avulla
MinRoll = -1 * MaxRoll

# Verrataan Roll -kulmaa MaxRoll ja MinRoll -arvoihin
Roll = max(MinRoll, min(Roll, MaxRoll))

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

# Tulostetaan arvot millimetreinä ja kierroksina
print("Vasemman servon pituus:", VasenServo, "mm")
print("Oikean servon pituus:", OikeaServo, "mm")
print()
print("Vasemman servon pituus:", VasenServo / (0.2 * 25.4))
print("Oikean servon pituus:", OikeaServo / (0.2 * 25.4))
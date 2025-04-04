import NiDAQ_controller
import time
import requests
SERVER_URL = "http://127.0.0.1:5001/"
joy = NiDAQ_controller.NiDAQJoysticks()

MAX_ROLL = 16
MAX_PITCH = 8.5
MAX_DIFF = 0.2

while True:
    try:
        time.sleep(0.05)
        values = joy.read()
        pitch = values[4] * (-1)
        roll = values[3] * (-1)
        button_pressed = values[18]

        if button_pressed == 1.0:
            print("button pressed!")
            roll = roll * MAX_ROLL
            pitch = pitch * MAX_PITCH
            roll_has_val = abs(roll) > MAX_DIFF
            pitch_has_val = abs(pitch) > MAX_DIFF

            if not roll_has_val:
                roll = 0.0
            if not pitch_has_val:
                pitch = 0.0

            ### make a command
            requests.get(SERVER_URL+"setvalues", {"pitch": pitch, "roll": roll} )
    except Exception as e:
        continue
        
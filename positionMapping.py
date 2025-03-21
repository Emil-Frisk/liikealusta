from pymodbus.client import AsyncModbusTcpClient
from address_enum import READ_ADDRESSES
import atexit
import struct
import requests

def convert_16bit_twos_complement(binary_data):
    # Assuming 'binary_data' is a bytes object containing the 16-bit integer
    # '>h' means big-endian ('>') short ('h') which is 16 bits in 2's complement
    number = struct.unpack('>h', binary_data)[0]
    return number


def cleanup():
    print("cleanup func executed!")
    client_left.close()
    client_right.close()

SERVER_URL = "http://127.0.0.1:5001/"

SERVER_IP_LEFT = '192.168.0.211'  
SERVER_IP_RIGHT = '192.168.0.212'
SERVER_PORT = 502  
client_left = AsyncModbusTcpClient(host=SERVER_IP_LEFT, port=SERVER_PORT)
client_right = AsyncModbusTcpClient(host=SERVER_IP_RIGHT, port=SERVER_PORT)

async def get_motor_pos(client):
    return await client.read_holding_registers(READ_ADDRESSES.pfeedback.value, 2)

async def main():
    atexit.register(cleanup)
    await client_left.connect()
    await client_right.connect()
    print("Connected to both motors")
    try:
        while(True):
            user_input = input("Press 'r' to read motor position values or 'x' to exit: \n Press 'l' to move left motor, Press 'r' to move right motor").lower()
            if (user_input == 'x'):
                break
            if (user_input == 'r'):
                motor1pos = get_motor_pos(client_left)
                motor2pos = get_motor_pos(client_right)

                desimaaliluku = motor1pos[0] # desimaalit
                kokonaisluku = motor1pos[1] # kokonaisluku

                print("Motor 1 kokonaisluku: " + kokonaisluku)
                print("Motor 1 desimaaliluku: " + desimaaliluku)
                print("Motor 1 position: " + motor1pos[1])
                print("Motor 2 position: " + motor2pos[1])
            if (user_input == "s"):
                requests.get(SERVER_URL+"stop")
            if (user_input == "l"):
                requests.get(SERVER_URL+"write", {"direction": "l"})
            if (user_input == "r"):
                requests.get(SERVER_URL+"write", {"direction": "r"})
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
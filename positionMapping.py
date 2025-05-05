from pymodbus.client import ModbusTcpClient
from address_enum import READ_ADDRESSES
import atexit
import struct
import requests

def shift_bits(number, shift_bit_amount):
        number = number & 0xffff
        result = number >> shift_bit_amount
        return result



SERVER_URL = "http://127.0.0.1:5001/"
SERVER_IP_LEFT="192.168.0.211"
SERVER_IP_RIGHT="192.168.0.212"
SERVER_PORT=502
client_leFt = ModbusTcpClient(host=SERVER_IP_LEFT, port=SERVER_PORT)
client_right = ModbusTcpClient(host=SERVER_IP_RIGHT, port=SERVER_PORT)

client_right.connect()
client_leFt.connect()

def main():
    
    print("Connected to both motors")
    try:
        while(True):
            user_input = input("Tuolin ohjaus rajapinta \n Paina e (eteenpäin) \n Paina t (taaksepäin) \n paina o (oikeelle) \n paina v (vasemmalle)").lower()
            if (user_input == 'y'):
                client_leFt.write_register(address=4001, value=1)
                client_right.write_register(address=4001, value=1)
            if user_input == 'k':
                pass
            if user_input == 'p':
                #Factory IPEAK - 1919
                response_left = client_leFt.read_holding_registers(address=9204, count=1)
                response_right = client_right.read_holding_registers(address=9204, count=1)

# I peak        #IPEAK - 2560 
                response_left = client_leFt.read_holding_registers(address=5108, count=1)
                response_right = client_right.read_holding_registers(address=5108, count=1)

                response_left = client_leFt.read_holding_registers(address=9205, count=1)
                response_right = client_right.read_holding_registers(address=9205, count=1)

                # Current operation mode
                response_left = client_leFt.read_holding_registers(address=31, count=1)
                response_right = client_right.read_holding_registers(address=31, count=1)

                ### analog input parameters options
                response_left = client_leFt.read_holding_registers(address=31, count=1)
                response_right = client_right.read_holding_registers(address=31, count=1)


                #### analog min min range
                response_left = client_leFt.read_holding_registers(address=7218, count=2)
                response_right = client_right.read_holding_registers(address=7218, count=2) 

                ### user mode 2 analog in min
                response_left = client_leFt.read_holding_registers(address=7210, count=2)
                response_right = client_right.read_holding_registers(address=7210, count=2) 

                ### user mode 2 analog in max
                response_left = client_leFt.read_holding_registers(address=7212, count=2)
                response_right = client_right.read_holding_registers(address=7212, count=2) 

                ### analog max range
                response_left = client_leFt.read_holding_registers(address=7220, count=2)
                response_right = client_right.read_holding_registers(address=7220, count=2) 

                  ### analog min adc range
                response_left = client_leFt.read_holding_registers(address=7214, count=2)
                response_right = client_right.read_holding_registers(address=7214, count=2)

                ### analog max adc range
                ### 15900
                response_left = client_leFt.read_holding_registers(address=7216, count=2)
                response_right = client_right.read_holding_registers(address=7216, count=2) 

                # current revolutions
                response_left = client_leFt.read_holding_registers(address=378, count=2)
                response_right = client_right.read_holding_registers(address=378, count=2) 

                # host control command mode
                response_left = client_leFt.read_holding_registers(address=4303, count=1)
                response_right = client_right.read_holding_registers(address=4303, count=1) 

                # analog i channel
                response_left = client_leFt.read_holding_registers(address=7101, count=1)
                response_right = client_right.read_holding_registers(address=7101, count=1) 

                # alt command mode
                response_left = client_leFt.read_holding_registers(address=5107, count=1)
                response_right = client_right.read_holding_registers(address=5107, count=1)

                 # defaul modet
                response_left = client_leFt.read_holding_registers(address=5106, count=1)
                response_right = client_right.read_holding_registers(address=5106, count=1)

                # IEG MODE
                response_left = client_leFt.read_holding_registers(address=4316, count=1) 
                response_right = client_right.read_holding_registers(address=4316, count=1)

                # IEG MOTION
                response_left = client_leFt.read_holding_registers(address=4317, count=1) 
                response_right = client_right.read_holding_registers(address=4317, count=1)

                #ANALOG POS MIN
                response_left = client_leFt.read_holding_registers(address=7102, count=2) 
                response_right = client_right.read_holding_registers(address=7102, count=2) 

                # ANALOG POS MAX
                response_left = client_leFt.read_holding_registers(address=7104, count=2)
                response_right = client_right.read_holding_registers(address=7104, count=2)

                 # VELOCITY 213 - 256
                response_left = client_leFt.read_holding_registers(address=7106, count=2)
                response_right = client_right.read_holding_registers(address=7106, count=2)
                
                # ACCEL
                response_left = client_leFt.read_holding_registers(address=7108, count=2) 
                response_right = client_right.read_holding_registers(address=7108, count=2)

                 # MODBUSCNTRL
                response_left = client_leFt.read_holding_registers(address=7188, count=1)
                response_right = client_right.read_holding_registers(address=7188, count=1)

                # client_leFt.write_register(address=7188, value=3000)
        

                # OEG sttus
                response_right = client_right.read_holding_registers(address=104, count=1)
                response_left = client_right.read_holding_registers(address=104, count=1)
                test1 = bin(response_left.registers[0])
                test2 = bin(response_right.registers[0])

                # home åpsition
                response_left = client_right.read_holding_registers(address=6002, count=2)
                response_right = client_right.read_holding_registers(address=6002, count=2)

                 # I peak factory
                response_left = client_leFt.read_holding_registers(address=9204, count=1)
                response_right = client_right.read_holding_registers(address=9204, count=1)

            if user_input == "å":
                ### mode 1 user low
                response_left = client_leFt.read_holding_registers(address=7202, count=2) 
                combine(response_left.registers)

            if (user_input == "s"):
                requests.get(SERVER_URL+"stop")
            if (user_input == "x"):
                a=10
                requests.get(SERVER_URL+"shutdown")
            if (user_input == "q"):
                requests.get(SERVER_URL+"setvalues", {"pitch": 0.0, "roll": -16} )

            if (user_input == "t"):
                requests.get(SERVER_URL+"write", {"pitch": "-"})
            if (user_input == "e"):
                requests.get(SERVER_URL+"write", {"pitch": "+"})
            if (user_input == "v"):
                requests.get(SERVER_URL+"write", {"roll": "-"})
            if (user_input == "o"):
                requests.get(SERVER_URL+"write", {"roll": "+"})
    except Exception as e:
        print(e)

def combine(registers):
    low_bum = registers[0]
    high_num = registers[1]
    shifted = high_num << 16
    # test = shifted | low_bum
    test = shifted
    a = 10
    b=wtf(test, 31)
    c=200

def wtf(value, bits):
    if value & (1 << (bits)):
        return value - (1 << bits)
    return value

if __name__ == "__main__":
     main()
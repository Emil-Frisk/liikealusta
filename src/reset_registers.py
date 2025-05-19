from pymodbus.client import ModbusTcpClient
import asyncio

SERVER_URL = "http://127.0.0.1:5001/"
SERVER_IP_LEFT="192.168.0.211"
SERVER_IP_RIGHT="192.168.0.212"
SERVER_PORT=502
client_leFt = ModbusTcpClient(host=SERVER_IP_LEFT, port=SERVER_PORT)
client_right = ModbusTcpClient(host=SERVER_IP_RIGHT, port=SERVER_PORT)

client_right.connect()
client_leFt.connect()
# Create exe
# pyinstaller -F reset_registers.py

def main():
        try:
            client_leFt.write_register(address=4001, value=1)
            client_right.write_register(address=4001, value=1)    
        except Exception as e:
            print(f"Reset failed: {e}")
            input()

if __name__ == "__main__":
     main()
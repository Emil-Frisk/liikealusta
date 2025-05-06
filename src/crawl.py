from pymodbus.client import ModbusTcpClient

server_url = "http://127.0.0.1:5001/"
right_client = "192.168.0.212"
server_port = 502
left_client =  ModbusTcpClient(host="192.168.0.211", port=server_port) 



def start():

def crawl():
    start_i = 2
    for i in range(12564):
        next_register = start_i + i
        left_client.read_holding_registers(count=1, address=i)


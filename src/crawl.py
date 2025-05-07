from pymodbus.client import AsyncModbusTcpClient
import os
import difflib
import asyncio

server_url = "http://127.0.0.1:5001/"
right_client = "192.168.0.212"
server_port = 502

async def connect():
    left_client =  AsyncModbusTcpClient(host="192.168.0.211", port=server_port) 
    await left_client.connect()
    return left_client

base_filename = "Registers data"
extension = ".txt"


"""Generate a unique filename by appending a number if the file exists."""
def get_unique_filename(base_filename, extension=".txt"):
    counter = 0
    new_name = f"{base_filename}{extension}"
    
    while os.path.exists(new_name):
        counter += 1
        new_name = f"{base_filename}({counter}){extension}"
    
    return new_name

def start():
    pass

def compare_files(file1, file2):
    """ Compare the files using difflib """
    with open(file1) as f1, open(file2) as f2:
        file1_lines = f1.readlines()
        file2_lines = f2.readlines()
        a = 12
    # Create a Differ object and compare the files
    differ = difflib.Differ()
    diff = list(differ.compare(file1_lines, file2_lines))
    
    # Write differences to the output file
    with open("changed_lines10.txt", 'a', encoding='utf-8') as out_file:
        for line in diff:
            if line.startswith(('+')):  # Include only added, removed, or hint lines
                out_file.write(line.strip()+"\n")
    
    print(f"Comparison complete.")
    


""""Reads all Tritex II register and writes them to a new file"""
async def crawl():
    filename = get_unique_filename(base_filename, extension)
    start_i = 2
    left_client = await connect()
    with open(filename, "a", encoding="utf-8") as file:
        for i in range(12564):
            success = False
            next_register = start_i + i
            try:
                result = await left_client.read_holding_registers(count=1, address=next_register)
                file.write(f"Register ID: {next_register} - Data: {result.registers[0]}\n")
                success = True
            except Exception as e:
                if not success:
                    file.write(f"Register ID: {next_register} - Data: NA\n")
                    continue
    print(f"Crawling compelete.")
                    
                
            
if __name__ == "__main__":
    async def run_app():
        await crawl() 

    compare_files("C:\liikealusta\Registers data.txt","C:\liikealusta\Registers data(1).txt")
    # asyncio.run(run_app())
        


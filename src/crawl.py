from pymodbus.client import ModbusTcpClient
import os
import difflib

server_url = "http://127.0.0.1:5001/"
right_client = "192.168.0.212"
server_port = 502
left_client =  ModbusTcpClient(host="192.168.0.211", port=server_port) 

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
    differ = difflib.Differ()
    diff = list(differ.compare(file1, file2))
    
    # Write differences to the output file
    with open("changed_lines.txt", 'w', encoding='utf-8') as out_file:
        differences_found = False
        for line in diff:
            if line.startswith('- ') or line.startswith('+ '):
                # Line removed (-), added (+), or changed (one of each)
                differences_found = True
                out_file.write(f"{line}\n")
            elif line.startswith('? '):
                # Indicates specific differences in a line (optional)
                differences_found = True
                out_file.write(f"Difference hint: {line}\n")
        
        if not differences_found:
            out_file.write("No differences found between the files.\n")
    print(f"Comparison complete.")
    


""""Reads all Tritex II register and writes them to a new file"""
def crawl():
    filename = get_unique_filename(base_filename, extension)
    start_i = 2
    with open(filename, "a", encoding="utf-8") as file:
        for i in range(12564):
            success = False
            next_register = start_i + i
            try:
                result = left_client.read_holding_registers(count=1, address=i)
                file.write(f"Register ID: {next_register} - Data: {result}\n")
                success = True
            except Exception as e:
                if not success:
                    file.write(f"Error reading register {next_register}: {e}\n")
                    continue
    print(f"Crawling compelete.")
                    
                
            

        


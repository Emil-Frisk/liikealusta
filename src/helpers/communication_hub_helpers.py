from utils.utils import extract_part

def validate_update_values(values):
    acc = int(values["acceleration"])
    vel = int(values["velocity"])
    if (vel < 0) or acc < 0:
        return False
    return True

def close_tasks(self):
    if hasattr(self, "monitor_fault_poller"):
        self.monitor_fault_poller.cancel()
        self.logger.info("Closed monitor fault poller")

def validate_pitch_and_roll_values(pitch,roll):
    try:
        # TODO validate values here
        pitch = float(pitch)
        roll = float(roll)
        return True
    except:
        raise
    
def validate_message(self,receiver, message):
    if not message:
        return (False, None, "event=error|message=Action message given, but no actual message found, example: message=<message>|")
    
    if not receiver:
        return (False, None, "event=error|message=No receiver given in the message, example: receiver=<receiver>|")

    for client, info in self.wsclients.items():
        if info["identity"] == receiver:
            return (True, client, message)
        
    return (False, None, "event=error|message=No receiver was found in the server with this identity|")

def extract_parts(msg): # example message: "action=STOP|receiver=startup|identity=fault_poller|message=CRITICAL FAULT!|pitch=40.3"
    receiver = extract_part("receiver=", message=msg)
    identity = extract_part("identity=", message=msg)
    message = extract_part("message=", message=msg)
    action = extract_part("action=", message=msg)
    pitch = extract_part("pitch=", message=msg)
    roll = extract_part("roll=", message=msg)
    event = extract_part("event=", message=msg)
    acceleration = extract_part("acc=", message=msg)
    velocity = extract_part("vel=", message=msg)

    ### if message has event append it to it
    if message and event:
        message = f"event={event}|message={message}|"

    return (receiver, identity, message,action,pitch,roll,acceleration,velocity)

import asyncio
import psutil

async def monitor_fault_poller(self):
    """
    Heathbeat monitor that makes sure fault poller
    stays alive and if it dies it restarts it
    """
    while True:
        if hasattr(self, 'fault_poller_pid'):
            pid = self.fault_poller_pid
            if pid and not psutil.pid_exists(pid):
                self.logger.warning(f"fault_poller (PID: {pid}) is not running, restarting...")
                new_pid = self.module_manager.launch_module("fault_poller")
                self.fault_poller_pid = new_pid
                self.logger.info(f"Restarted fault_poller with PID: {new_pid}")
                del self.module_manager.processes[pid]
        await asyncio.sleep(10)  # Check every 10 seconds

async def monitor_socket_server(self):
    """
    Heathbeat monitor that makes sure socket server     
    stays alive and if it dies it restarts it
    """
    while True:
        if hasattr(self, 'so_srv_pid'):
            pid = self.so_srv_pid
            if pid and not psutil.pid_exists(pid):
                self.logger.warning(f"socket server (PID: {pid}) is not running, restarting...")
                new_pid = self.module_manager.launch_module("websocket_server")
                self.so_srv_pid = new_pid
                self.logger.info(f"Restarted websocket server with PID: {new_pid}")
                del self.module_manager.processes[pid]
        await asyncio.sleep(60)

async def create_hearthbeat_monitor_tasks(self, module_manager):
    fault_poller_pid = module_manager.launch_module("fault_poller")
    self.fault_poller_pid = fault_poller_pid
    self.monitor_fault_poller = asyncio.create_task(monitor_fault_poller(self))

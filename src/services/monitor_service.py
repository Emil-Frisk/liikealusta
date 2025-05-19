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

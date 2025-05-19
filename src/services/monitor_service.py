import asyncio
import psutil

async def monitor_fault_poller(app):
    """
    Heathbeat monitor that makes sure fault poller
    stays alive and if it dies it restarts it
    """
    while True:
        if hasattr(app, 'fault_poller_pid'):
            pid = app.fault_poller_pid
            if pid and not psutil.pid_exists(pid):
                app.logger.warning(f"fault_poller (PID: {pid}) is not running, restarting...")
                new_pid = app.module_manager.launch_module("fault_poller")
                app.fault_poller_pid = new_pid
                app.logger.info(f"Restarted fault_poller with PID: {new_pid}")
                del app.module_manager.processes[pid]
        await asyncio.sleep(10)  # Check every 10 seconds

async def monitor_socket_server(app):
    """
    Heathbeat monitor that makes sure socket server 
    stays alive and if it dies it restarts it
    """
    while True:
        if hasattr(app, 'so_srv_pid'):
            pid = app.so_srv_pid
            if pid and not psutil.pid_exists(pid):
                app.logger.warning(f"socket server (PID: {pid}) is not running, restarting...")
                new_pid = app.module_manager.launch_module("websocket_server")
                app.so_srv_pid = new_pid
                app.logger.info(f"Restarted websocket server with PID: {new_pid}")
                del app.module_manager.processes[pid]
        await asyncio.sleep(60)

async def create_hearthbeat_monitor_tasks(app, module_manager):
    fault_poller_pid = module_manager.launch_module("fault_poller")
    app.fault_poller_pid = fault_poller_pid
    # so_srv_pid = module_manager.launch_module("websocket_server")
    # app.so_srv_pid = so_srv_pid
    app.monitor_fault_poller = asyncio.create_task(monitor_fault_poller(app))
    # app.monitor_so_srv = asyncio.create_task(monitor_socket_server(app))
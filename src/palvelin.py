import psutil
import asyncio
from quart import Quart, request, make_response, jsonify
from ModbusClients import ModbusClients
import atexit
from utils.setup_logging import setup_logging
from launch_params import handle_launch_params
from module_manager import ModuleManager
import subprocess
from time import sleep 
from services.monitor_service import create_hearthbeat_monitor_tasks
from services.cleaunup import cleanup, close_tasks, shutdown_server
from services.motor_service import configure_motor
from services.motor_control import demo_control, rotate
from utils.utils import is_nth_bit_on, IEG_MODE_bitmask_enable, convert_acc_rpm_revs, convert_vel_rpm_revs, convert_to_revs
import math
import sys
import os
import time

async def init(app):
    try:
        logger = setup_logging("server", "server.log")
        app.logger = logger
        module_manager = ModuleManager(logger)
        app.module_manager = module_manager
        config = handle_launch_params()
        clients = ModbusClients(config=config, logger=logger)

        await create_hearthbeat_monitor_tasks(app, module_manager)

        # Connect to both drivers
        connected = await clients.connect() 
        app.clients = clients

        if not connected:  
            logger.error(f"""could not form a connection to both motors,
                          Left motors ips: {config.SERVER_IP_LEFT}, 
                          Right motors ips: {config.SERVER_IP_RIGHT}, 
                         shutting down the server """)
            cleanup(app)

        app.app_config = config
        app.is_process_done = True

        atexit.register(lambda: cleanup(app))
        await configure_motor(app.clients, config)
        

    except Exception as e:
        logger.error(f"Initialization failed: {e}")


async def create_app():
    app = Quart(__name__)
    await init(app)

    @app.route("/write", methods=['get'])
    async def write():
        pitch = request.args.get('pitch')
        roll = request.args.get('roll') 
        
        await demo_control(pitch, roll)
    
    @app.route('/shutdown', methods=['get'])
    async def shutdown():
        """Shuts down the server when called."""
        app.logger.info("Shutdown request received.")
        await shutdown_server(app)

    @app.route('/stop', methods=['get'])
    async def stop_motors():
        try:
            success = await app.clients.stop()
            if not success:
                pass # do something crazy :O
        except Exception as e:
            app.logger.error("Failed to stop motors?") # Mitäs sitten :D

    @app.route('/setvalues', methods=['GET'])
    async def calculate_pitch_and_roll():#serverosote/endpoint?nimi=value&nimi2=value2
        # Get the two float arguments from the query parameters
        pitch = float(request.args.get('pitch'))
        roll = float(request.args.get('roll'))
        await rotate(pitch, roll)


    return app
if __name__ == '__main__':
    async def run_app():
        app = await create_app()
        await app.run_task(port=app.app_config.WEB_SERVER_PORT)

    asyncio.run(run_app())
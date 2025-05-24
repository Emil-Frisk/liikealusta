import psutil
import asyncio
from quart import Quart, request, make_response, jsonify
from ModbusClients import ModbusClients
import atexit
from utils.setup_logging import setup_logging
from utils.launch_params import handle_launch_params
from services.process_manager import ModuleManager
from time import sleep 
from services.monitor_service import create_hearthbeat_monitor_tasks
from services.cleaunup import cleanup, close_tasks, disable_server, shutdown_server_delay
from services.motor_service import configure_motor,set_motor_values
from services.motor_control import demo_control, rotate
from services.validation_service import validate_update_values
from utils.utils import is_nth_bit_on, IEG_MODE_bitmask_enable, convert_acc_rpm_revs, convert_vel_rpm_revs, convert_to_revs

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
        return jsonify(""), 204
    
    @app.route('/shutdown', methods=['get'])
    async def shutdown():
        """Shuts down the server when called."""
        app.logger.info("Shutdown request received.")
        await disable_server(app)
        
        # Schedule shutdown after response
        asyncio.create_task(shutdown_server_delay(app))
        
        # Return success response immediately
        return jsonify({"status": "success"}), 200
        

    @app.route('/stop', methods=['get'])
    async def stop_motors():
        try:
            success = await app.clients.stop()
            if not success:
                pass # do something crazy :O
        except Exception as e:
            app.logger.error("Failed to stop motors?") # Mitäs sitten :D
        return jsonify(""), 204

    @app.route('/setvalues', methods=['GET'])
    async def calculate_pitch_and_roll():#serverosote/endpoint?nimi=value&nimi2=value2
        # Get the two float arguments from the query parameters
        pitch = float(request.args.get('pitch'))
        roll = float(request.args.get('roll'))
        await rotate(pitch, roll)
        return jsonify(""), 204

    @app.route('/updatevalues', methods=['get'])
    async def update_input_values():
        try:
            values = request.args.to_dict()
            if not validate_update_values(values):
                raise ValueError()

            if values:
                await set_motor_values(values,app.clients)
            
            return jsonify(""), 204
        except ValueError as e:
            return jsonify({"status": "error", "message": "Velocity and Acceleration has to be positive integers"}), 400
        except Exception as e:
            print(e)
    return app
if __name__ == '__main__':
    async def run_app():
        app = await create_app()
        await app.run_task(port=app.app_config.WEB_SERVER_PORT)

    asyncio.run(run_app())
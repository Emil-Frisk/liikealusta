import asyncio
from services.cleaunup import cleanup, close_tasks, disable_server, shutdown_server_delay
from services.motor_service import configure_motor,set_motor_values
from services.motor_control import demo_control, rotate
from services.validation_service import validate_update_values

async def shutdown(self, wsclient=None):
    """Shuts down the server when called."""
    self.logger.info("Shutdown request received.")
    await disable_server(self, wsclient)
    
async def stop_motors(self):
    try:
        success = await self.clients.stop()
        if not success:
            pass # do something crazy :O
    except Exception as e:
        self.logger.error("Failed to stop motors?") # Mitäs sitten :D
    return {"status": "success"}

async def calculate_pitch_and_roll(pitch, roll):#serverosote/endpoint?nimi=value&nimi2=value2
    # Get the two float arguments from the query parameters
    
    await rotate(pitch, roll)

async def update_input_values(self,acceleration,velocity):
    try:
        values = {acceleration: acceleration, velocity: velocity}
        if not validate_update_values(values):
            raise ValueError()

        if values:
            await set_motor_values(values,self.clients)
            return {"status":"success"}
    except ValueError as e:
        return {"status": "error", "message": "Velocity and Acceleration has to be positive integers"}
    except Exception as e:
        print(e)
import asyncio
from services.cleaunup import cleanup, close_tasks, disable_server, shutdown_server_delay
from services.motor_service import configure_motor,set_motor_values
from services.motor_control import demo_control, rotate
from services.validation_service import validate_update_values

async def shutdown(self, wsclient=None):
    """Shuts down the server when called."""
    self.logger.info("Shutdown request received.")
    
    """stops and disables motors and closes sub processes"""
    self.logger.info("Shutdown request received. Cleaning up...")

    try:
        success = await self.clients.stop()
        if not success:
            self.logger.error("Stopping motors was not successful, will not shutdown server")
            return
    except Exception as e:
        self.logger.error("Stopping motors was not successful, will not shutdown server")
        return
    #########################################################################################
    #########################################################################################
    ####NOTE DO NOT REMOVE THIS LINE -IMPORTANT FOR MOTORS TO HAVE TO TO STOP################
    await asyncio.sleep(5)
    #########################################################################################
    #########################################################################################
    #########################################################################################

    await self.clients.reset_motors()
    await asyncio.sleep(20)

    if wsclient:
        await wsclient.send("event=shutdown|message=Server has been shutdown.|")
    
    self.logger.info("cleanup function executed!")
    close_tasks(self)
    self.module_manager.cleanup_all()
    if self.clients is not None:
        self.clients.cleanup()

    self.logger.info("Cleanup complete. Shutting down server.")
    
    if hasattr(self, "shutdown_ws_server"):
        await self.shutdown_ws_server()

    
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
import asyncio
import os

async def disable_server(self):    
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
    await asyncio.sleep(5)

    await self.clients.reset_motors()

    await cleanup(self, False)
    
async def shutdown_server_delay(self):
    # Stop the Quart self's event loop
    await asyncio.sleep(1)
    
    self.logger.info("Server shutdown complete.")
    os._exit(0)

def close_tasks(self):
    if hasattr(self, "monitor_fault_poller"):
        self.monitor_fault_poller.cancel()
        self.logger.info("Closed monitor fault poller")

async def cleanup(self, shutdown=True):
    #### TODO - fault poller ja skct wseruv  ei samma
    self.logger.info("cleanup function executed!")
    close_tasks(self)
    self.module_manager.cleanup_all()
    if self.clients is not None:
        self.clients.cleanup()

    self.logger.info("Cleanup complete. Shutting down server.")
    await self.shutdown_ws_server()
    if shutdown:
        os._exit(0)
    
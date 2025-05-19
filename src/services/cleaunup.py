import asyncio
import os

async def disable_server(app):    
    """stops and disables motors and closes sub processes"""
    app.logger.info("Shutdown request received. Cleaning up...")

    try:
        success = await app.clients.stop()
        if not success:
            app.logger.error("Stopping motors was not successful, will not shutdown server")
            return
    except Exception as e:
        app.logger.error("Stopping motors was not successful, will not shutdown server")
        return
    await asyncio.sleep(5)

    await app.clients.reset_motors()

    cleanup(app, False)
    
async def shutdown_server_delay(app):
    # Stop the Quart app's event loop
    await asyncio.sleep(1)
    
    app.logger.info("Server shutdown complete.")
    os._exit(0)

def close_tasks(app):
    if hasattr(app, "monitor_fault_poller"):
        app.monitor_fault_poller.cancel()
        app.logger.info("Closed monitor fault poller")

def cleanup(app, shutdown=True):
    #### TODO - fault poller ja skct wseruv  ei samma
    app.logger.info("cleanup function executed!")
    close_tasks(app)
    app.module_manager.cleanup_all()
    if app.clients is not None:
        app.clients.cleanup()

    app.logger.info("Cleanup complete. Shutting down server.")
    app.shutdown_ws_server()
    if shutdown:
        os._exit(0)
    
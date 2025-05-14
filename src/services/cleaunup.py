import asyncio
import os

async def shutdown_server(app):    
    """Gracefully shuts down the server."""
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

    # Cleanup Modbus clients
    cleanup(app)
    
def close_tasks(app):
    if hasattr(app, "monitor_fault_poller"):
        app.monitor_fault_poller.cancel()
        app.logger.info("Closed monitor fault poller")
    if hasattr(app, "monitor_so_srv"):
        app.monitor_so_srv.cancel()
        app.logger.info("Closed monitor socket server")

def cleanup(app):
    app.logger.info("cleanup function executed!")
    close_tasks(app)
    app.module_manager.cleanup_all()
    if app.clients is not None:
        app.clients.cleanup()

    app.logger.info("Cleanup complete. Shutting down server.")
    os._exit(0)
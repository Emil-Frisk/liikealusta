import asyncio
from CommunicationHub import CommunicationHub

async def main():
    try:
        hub = CommunicationHub()
        ### TODO - run hub.init() only after gui identification 
        ### so it can be communicated if there is a fault
        # await hub.init()

        await hub.start_server()
        while True:
            await asyncio.sleep(3600)

    except KeyboardInterrupt:
        print("Keyboard interrupt -> shutting down the server...")
    finally:
        await hub.shutdown_server()
        
if __name__ == "__main__":
    asyncio.run(main())

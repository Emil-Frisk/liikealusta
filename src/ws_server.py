import asyncio
import websockets
import json

async def handle_connection(websocket, path):
    print("Client connected")
    try:
        async for message in websocket:
            print(f"Received: {message}")
            response = {"status": "received", "message": message}
            await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def send_message(websocket):
    while True:
        await asyncio.sleep(5)
        message = {
            "command": "update_status",
            "status": "System running"
        }
        await websocket.send(json.dumps(message))

async def main():
    server = await websockets.serve(handle_connection, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    async with websockets.connect("ws://localhost:8765") as ws:
        await send_message(ws)
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
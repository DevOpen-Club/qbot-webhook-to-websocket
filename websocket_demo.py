import asyncio
import websockets

async def connect_to_websocket(secret):
    uri = f"ws://ooo.docb.cn/ws/{secret}"  # 需要替换为您的WebSocket服务器地址和port
    async with websockets.connect(uri) as websocket:
        print(f"Connected to WebSocket with secret: {secret}")

        # # 发送一条消息，可以根据需要更改发送内容
        # await websocket.send("Hello, WebSocket!")

        # 持续接收消息
        try:
            while True:
                response = await websocket.recv()
                print(f"Received message: {response}")
        except Exception as e:
            print(f"Connection closed with exception: {e}")

if __name__ == "__main__":
    secret = "ixxxxxxxxxxxxxxxFnMvU3cB"  # 替换为实际的secret
    asyncio.run(connect_to_websocket(secret))

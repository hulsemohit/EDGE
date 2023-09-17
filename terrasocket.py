import numpy as np
import time
import asyncio
import json
import websockets
import httpx

WS_CONNECTION = "wss://ws.tryterra.co/connect"

async def get_token():
    url = 'https://ws.tryterra.co/auth/developer'
    headers = {
        'accept': 'application/json',
        'dev-id': 'mit-testing-tsJPcfZPlr',
        'x-api-key': 'AiOcd472nLnBgV6h7pUf9LLro3Mf6Bl2',
    }

    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(url, headers=headers)
            token_resp.raise_for_status()
            token_data = token_resp.json()
            return token_data["token"]
    except Exception as e:
        print(e)
    return ""

vec = np.array([0, 0, 0])

async def init_ws(token):
    async def heart_beat():
        nonlocal expecting_heart_beat_ack
        if expecting_heart_beat_ack:
            await websocket.close()
        heart_beat_payload = json.dumps({"op": 0})
        await websocket.send(heart_beat_payload)
        print("↑  " + heart_beat_payload)
        expecting_heart_beat_ack = True

    expecting_heart_beat_ack = False

    async with websockets.connect(WS_CONNECTION) as websocket:
        print("Connection Established")
        print(websocket)

        last_pinged = time.time() 
        interval = 40000 / 1000
        while True:
            try:
                message = await websocket.recv()
                print("↓  " + message)
                msg = json.loads(message)
                if "d" in msg and "d" in msg["d"]:
                    vec = np.array(msg["d"]["d"])

                if time.time() - last_pinged > interval:
                    last_pinged = time.time()
                    await heart_beat()                    

                if msg["op"] == 2:
                    await heart_beat()
                    interval = msg["d"]["heartbeat_interval"] / 1000
                    payload = json.dumps({
                        "op": 3,
                        "d": {
                            "token": token,
                            "type": 1  # 0 for user, 1 for developer
                        }
                    })
                    await websocket.send(payload)
                if msg["op"] == 1:
                    expecting_heart_beat_ack = False
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

async def main():
    token = await get_token()
    await init_ws(token)

if __name__ == "__main__":
    asyncio.run(main())


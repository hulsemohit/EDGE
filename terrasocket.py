import numpy as np
import time
import asyncio
import json
import websockets
import httpx
from datetime import datetime

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
        prev_timestamp = 0
        interval = 40000 / 1000
        while True:
            try:
                message = await websocket.recv()
                msg = json.loads(message)
                acc_data = "d" in msg and "d" in msg["d"]
                if acc_data:
                    vec = msg["d"]["d"]
                    ts = msg["d"]["ts"]
                    # get ts from datetime to timestamp
                    try: 
                        stamp = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
                        if stamp - prev_timestamp < 0.01:
                            acc_data = False
                        else: prev_timestamp = stamp
                    except:
                        print("fucked, might cause problem with spacing")
                        acc_data = False
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
                if acc_data:
                    with open("terra_output.log", "a") as f:
                        f.write(f'{{"x": {vec[0]}, "y": {vec[1]}, "z": {vec[2]}, "timestamp": {stamp}}}\n')
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

async def main():
    token = await get_token()
    await init_ws(token)

if __name__ == "__main__":
    asyncio.run(main())


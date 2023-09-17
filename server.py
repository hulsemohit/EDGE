from modal import asgi_app
from modal_image import image, stub

if stub.is_inside():
    import os
    from pydantic import BaseModel
    import numpy as np
    from fastapi import FastAPI, WebSocket
    from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
    from fastapi import File, UploadFile, BackgroundTasks
    import subprocess
    import wave
    import json
    import shutil

    from tqdm import tqdm
    from functools import partialmethod
    tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)

    import sys
    sys.path.append("EDGE")
    from interface import generate

def apply_fft(data):
    arr = np.array(data)
    x, y, z = arr[:, 0], arr[:, 1], arr[:, 2]
    x -= np.mean(x)
    y -= np.mean(y)
    z -= np.mean(z)
    fft = np.fft.fft
    combined = np.absolute(fft(x)) ** 2 + np.absolute(fft(y)) ** 2 + np.absolute(fft(z)) ** 2
    index = np.argmax(combined)
    freq = np.fft.fftfreq(len(combined))[index]
    period = 0.08 * 1 / freq # todo: change to actual width spacing
    return abs(period)

def close_data(mo_data, w_data, timestamp):
    period = apply_fft(mo_data)
    # get mean distance between beats, and compare to period (not using apply_fft
    w_period = 0
    for i in range(1, len(w_data)):
        w_period += w_data[i] - w_data[i-1]
    w_period /= len(w_data)
    print("[info]", "server:compare", "music:", 60 / w_period, "user:", 60 / period)
    return abs(period - w_period) < 0.1

def call_model():
    generate("sounds.wav")


@stub.function(image=image,gpu="a100",memory=16384,concurrency_limit=1)
@asgi_app()
def fastapi_app():
    subprocess.Popen(["python3", "EDGE/terrasocket.py"])

    web_app = FastAPI()
    music_beats = []
    existing_wavs = []

    @web_app.post("/uploadfile/")
    async def create_upload_file(file: UploadFile, background_tasks: BackgroundTasks):
        print("[info]", "server:uploadfile:", "received audio snippet")

        wav = file.file
        timestamp = 0

        with open("terra_output.log", "r") as f:
            user_data = []
            for l in f.readlines():
                d = json.loads(l)
                user_data.append([d["x"], d["y"], d["z"]])

        print("[info]", "server:uploadfile:", "performing beat matching on", len(user_data), "datapoints")

        with open("recent.wav", "wb") as f:
            shutil.copyfileobj(wav, f)
        os.system("DBNBeatTracker single -o beats.txt recent.wav")
        with open("beats.txt", "r") as f:
            music_beats = [timestamp + float(x) for x in f.read().splitlines()]


        is_user_in_sync = len(user_data) <= 1 or close_data(user_data, music_beats, timestamp)

        with wave.open("recent.wav", 'rb') as w:
            existing_wavs.append([w.getparams(), w.readframes(w.getnframes())])

        print("[info]", "server:uploadfile:", "existing waves: ", len(existing_wavs))

        while len(existing_wavs) > 3: existing_wavs.pop(0)

        if len(existing_wavs) == 3:
            with wave.open("sounds.wav", 'wb') as output:
                output.setparams(existing_wavs[0][0])
                output.writeframes(existing_wavs[0][1])
                output.writeframes(existing_wavs[1][1])
                output.writeframes(existing_wavs[2][1])

            print("[info]", "server:uploadfile:", "generating new dance")
            background_tasks.add_task(call_model)

        print("[info]", "server:uploadfile", "reached end of create_upload_file")
        return PlainTextResponse(str(is_user_in_sync))

    @web_app.get("/getmoves/")
    async def get_moves():
        if os.path.exists("render/test_sounds.mp4"):
            print("[info]", "server:getmoves:", "sending gif")
            return FileResponse("render/test_sounds.gif")
        else:
            print("[warn]", "server:getmoves:", "cannot send gif, still rendering")
            return FileResponse("render/loading.gif")

    return web_app

from modal import asgi_app
from modal_image import image, stub

if stub.is_inside():
    import os
    from pydantic import BaseModel
    import numpy as np
    from fastapi import FastAPI, WebSocket
    from fastapi.responses import HTMLResponse
    from fastapi import File, UploadFile, BackgroundTasks
    import subprocess
    import wave

    from EDGE.interface import generate

def apply_fft(data):
    arr = np.array(data[-100:])
    x, y, z = arr[:, 0], arr[:, 1], arr[:, 2]
    x -= np.mean(x)
    y -= np.mean(y)
    z -= np.mean(z)
    fft = np.fft.fft
    combined = np.absolute(fft(x)) ** 2 + np.absolute(fft(y)) ** 2 + np.absolute(fft(z)) ** 2
    index = np.argmax(combined)
    freq = np.fft.fftfreq(len(combined))[index]
    period = 0.08 * 1 / freq # todo: change to actual width spacing
    return period

def close_data(mo_data, w_data, timestamp):
    period = apply_fft(mo_data)
    # get mean distance between beats, and compare to period (not using apply_fft
    w_period = 0
    for i in range (1, len(w_data)):
        w_period += w_data[i][1] - w_data[i-1][1]
    w_period /= len(w_data)
    return abs(period - w_period) < 0.1

def call_model():
    generate("sounds.wav")


@stub.function(image=image)
@asgi_app()
def fastapi_app():
    subprocess.Popen(["python3", "EDGE/terrasocket.py"])

    class WavData(BaseModel):
        file: UploadFile
        timestamp: int

    web_app = FastAPI()
    music_beats = []
    existing_wavs = []

    @web_app.post("/uploadfile/")
    async def create_upload_file(wav: WavData, background_tasks: BackgroundTasks):
        f = wav.file
        outfile = "sounds.wav"

        if len(existing_wavs > 2):
            existing_wavs.pop(0)
        existing_wavs.append(f)
        data = []
        for file in existing_wavs:
            w = wave.open(file, 'rb')
            data.append([w.getparams(), w.readframes(w.getnframes())])
            w.close()

        output = wave.open(outfile, 'wb')
        output.setparams(data[0][0])
        output.writeframes(data[0][1])
        output.writeframes(data[1][1])
        output.close()

        background_tasks.add_task(call_model)

        with open("recent.wav", "wb") as buffer:
            shutil.copyfileobj(f, buffer)
        os.system("DBNBeatTracker -single recent.wav -o beats.txt")
        with open("beats.txt", "r") as f:
            music_beats += [timestamp + float(x) for x in f.read().splitlines()]
        with open("terra_output.log", "r") as f:
            data = f.read().splitlines()
        if not close_data(data, music_beats, wav.timestamp):
            return False
        return True
    return web_app

    @web_app.get("/")
    async def generate_dance():
        pass
    return web_app

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

    import sys
    sys.path.append("EDGE")
    from interface import generate

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
    print("INFO:", "call_model()")
    generate("sounds.wav")


@stub.function(image=image)
@asgi_app()
def fastapi_app():
    subprocess.Popen(["python3", "EDGE/terrasocket.py"])

    class WavData(BaseModel):
        file: UploadFile
 #       timestamp: int

    web_app = FastAPI()
    music_beats = []
    existing_wavs = []

    @web_app.post("/uploadfile/")
    async def create_upload_file(wavfile: UploadFile, background_tasks: BackgroundTasks):
        print("INFO:", "create_upload_file()")

        wav = wavfile.file
        timestamp = 0

        # Beat tracking
        with open("recent.wav", "wb") as f:
            shutil.copyfileobj(wav, f)
        os.system("DBNBeatTracker -single recent.wav -o beats.txt")
        with open("beats.txt", "r") as f:
            music_beats += [timestamp + float(x) for x in f.read().splitlines()]

        with open("terra_output.log", "r") as f:
            user_data = f.read().splitlines()

        is_user_in_sync = close_data(user_data, music_beats, timestamp)

        # Combine wavs into sounds.wav
        existing_wavs.append(wav)
        print("INFO:", "existing waves: ", len(existing_wavs))

        while len(existing_wavs) > 2: existing_wavs.pop(0)

        if len(existing_wavs) >= 2:
            combined = []
            for f in existing_wavs:
                w = wave.open(f, 'rb')
                combined.append([w.getparams(), w.readframes(w.getnframes())])
                w.close()

            output = wave.open("sounds.wav", 'wb')
            output.setparams(data[0][0])
            output.writeframes(data[0][1])
            output.writeframes(data[1][1])
            output.close()

            # Call model flask api background_tasks
            background_tasks.add_task(call_model)

        print("INFO:", "reached end of create_upload_file")
        return is_user_in_sync

    return web_app

    @web_app.get("/")
    async def get_dance():
        pass
    return web_app

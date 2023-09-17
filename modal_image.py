import modal

stub = modal.Stub("cygnus")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("software-properties-common")
    .apt_install("git")
    .apt_install("wget")
    .apt_install("curl")
    .apt_install("ffmpeg")
    .pip_install("youtube-dl")
    .pip_install("wandb")
    .pip_install("tqdm")
    .pip_install("matplotlib")
    .pip_install("soundfile")
    .pip_install("librosa")
    .pip_install("accelerate")
    .pip_install("einops")
    .pip_install("p_tqdm")
    .pip_install("git+https://github.com/facebookresearch/pytorch3d.git")
    .pip_install("git+https://github.com/rodrigo-castellon/jukemirlib.git")
    .pip_install("Cython")
    .pip_install("numpy")
    .run_commands(["pip install --upgrade --no-deps --force-reinstall --quiet 'git+https://github.com/CPJKU/madmom.git'"])
    .pip_install("fastapi")
    .pip_install("httpx")
    .pip_install("wave")
    .pip_install("numpy")
    .pip_install("python-multipart")
    .pip_install("websockets")
    .run_commands(["touch lol40"])
    .run_commands(["git clone https://github.com/hulsemohit/EDGE ~/EDGE"])
    .run_commands(["cd root/EDGE && bash download_model.sh"])
)

@stub.function(image=image,gpu="a100",memory=16384,cpu=8.0)
def main():
    pass

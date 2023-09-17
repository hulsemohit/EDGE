import glob
import os
from tempfile import TemporaryDirectory

import numpy as np
import torch
from tqdm import tqdm

from data.slice import slice_audio
from EDGE import EDGE
from data.audio_extraction.baseline_features import extract as baseline_extract
from data.audio_extraction.jukebox_features import extract as juke_extract

# Adaptation of test
# feature_type = "baseline" or "jukebox"
def generate(wav_file, feature_type="jukebox"):
    feature_func = juke_extract if feature_type == "jukebox" else baseline_extract
    sample_length = 30
    sample_size = int(sample_length / 2.5) - 1

    temp_dir = TemporaryDirectory()
    dirname = temp_dir.name

    print(f"Slicing {wav_file}")
    slice_audio(wav_file, 2.5, 5.0, dirname)
    file_list = sorted(glob.glob(f"{dirname}/*.wav"), key=stringintkey)

    rand_idx = random.randint(0, len(file_list) - sample_size)
    cond_list = []

    print(f"Computing features for {wav_file}")
    for idx, file in enumerate(tqdm(file_list)):
        if not (rand_idx <= idx < rand_idx + sample_size):
            continue
        reps, _ = feature_func(file)
        cond_list.append(reps)
    cond_list = torch.from_numpy(np.array(cond_list))

    model = EDGE(feature_type, f"checkpoint-{feature_type}.pt")
    model.eval()

    print("Generating dances")
    data_tuple = None, cond_list, file_list[rand_idx : rand_idx + sample_size]
    model.render_sample(
        data_tuple, "test", "render", render_count=-1, fk_out=None, render=True
    )
    print("Done")

    torch.cuda.empty_cache()
    temp_dir.cleanup()


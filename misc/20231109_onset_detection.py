import sounddevice as sd
import numpy as np
import socket
import librosa
import sys
import math
import matplotlib.pyplot as plt
import time as ti

sr = 22050
data_length = 1
data = np.zeros(int(sr)*data_length, dtype=np.float32)
onset_frames = []
detected_onset_time = []
non_negative_data = np.zeros(int(sr), dtype=np.float32)
shift_size = 576
#shift_size = 1136
hop_length = 128
frame_length = 256
pre_max = 30 / 1000 * sr // hop_length
post_max = 0 / 1000 * sr // hop_length + 1
pre_avg = 100 / 1000 * sr // hop_length
post_avg = 100 / 1000 * sr // hop_length + 1
wait = 300 / 1000 * sr // hop_length
#delta = 0.07
delta = 0.4


def callback_pitch(indata, frames, time, status):
    global data, onset_frames, non_negative_data, start_time, full_data
    data = np.roll(data, -shift_size, axis=0)
    data[-shift_size:] = indata.reshape((shift_size,))
    #all_data_list.append(indata.reshape((shift_size,)).copy())
    #full_data = np.roll(full_data, -shift_size, axis=0)
    #full_data[-shift_size:] = indata.reshape((shift_size,))

    src = data.reshape(data.size) * 100
    #rms = librosa.feature.rms(y=src, frame_length=frame_length, hop_length=hop_length, center=True)
    rms = librosa.feature.rms(y=src, frame_length=frame_length, hop_length=hop_length, center=False)
    onset_envelope = rms[0, 1:] - rms[0, :-1]
    onset_envelope = np.maximum(0.0, onset_envelope)
    onset_frames = librosa.util.peak_pick(onset_envelope, pre_max=pre_max, post_max=post_max, pre_avg=pre_avg, post_avg=post_avg, delta=delta, wait=wait)
    
    if len(onset_frames) != 0:
        _times = librosa.times_like(onset_envelope, sr=sr, hop_length=hop_length)
        for onset_frame in onset_frames:
            elapsed_time = (ti.time() - start_time) - (data_length - _times[onset_frame])
            
            if any(abs(elapsed_time - t) < 1.0 for t in detected_onset_time):
                continue
                
            detected_onset_time.append(elapsed_time)
            
            print(f"detect onset: {elapsed_time}")


input_device = int(input("input device number: "))
output_device = int(input("output device number: "))

sd.default.device = [input_device, output_device]

print("input device: ", sd.query_devices(kind="input")["name"], "\n")
print("output device: ", sd.query_devices(kind="output")["name"], "\n")

duration = int(input("duratino: "))

full_data = np.zeros(int(sr)*duration, dtype=np.float32)


with sd.InputStream(
            samplerate=sr,
            channels=1,
            dtype='float32',
            callback=callback_pitch
        ):
        start_time = ti.time()
        sd.sleep(int(duration * 1000))
        print(ti.time() - start_time)
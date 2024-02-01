""" UserEvaluation main file

* システム全体のユーザー評価実験のアプリケーションサーバー用ファイル

ToDo:
    - 事前準備
        - 使用するモデルを/models/に配置する
        - PCにオーディオインターフェースを接続する
        - ギターとオーディオインターフェースを接続する
    - HoloLens2側でアプリケーションを実行する前にサーバーを起動させる
    - sounddeviceで設定するオーディオドライバーを適切なものを選択する

"""

# ライブラリのインポート
import sounddevice as sd
import numpy as np
import socket
import librosa
import sys
import math
import matplotlib.pyplot as plt
import time as ti
import datetime
import configparser
import ast

import tensorflow
from tensorflow import keras
from keras.models import load_model

from libs import function1
from libs import function2
from libs import utilities

#　モデルのロード
print("model loading -----")
model = load_model("./../models/model.hdf5")
print("model loading -----")

config = configparser.ConfigParser()
config.read("config/config.ini", encoding='utf-8')
settings = config['SETTINGS']

frequency_array = np.array(settings['FREQUENCY_ARRAY'])
frequency2notename_dictionary = ast.literal_eval(settings['FREQUENCY2NOTENAME_DICTIONARY'])
expected_note_times = list(settings['EXPECTED_NOTE_TIMES'])
Asus4onE_chord_list = list(settings['CHORD_LIST_ASUS4ONE'])

SAMPLING_RATE = settings['SAMPLING_RATE']
SHIFT_SIZE = settings['SHIFT_SIZE']
DATA_LENGTH = settings['DATA_LENGTH']
HOP_LENGTH = settings['HOP_LENGTH']
FRAME_LENGTH = settings['FRAME_LENGTH']
DELTA = settings['DELTA']

sr = float(SAMPLING_RATE)
shift_size = float(SHIFT_SIZE)
data_length = float(DATA_LENGTH)
hop_length = float(HOP_LENGTH)
frame_length = float(FRAME_LENGTH)
pre_max = 30 / 1000 * sr // hop_length
post_max = 0 / 1000 * sr // hop_length + 1
pre_avg = 100 / 1000 * sr // hop_length
post_avg = 100 / 1000 * sr // hop_length + 1
wait = 300 / 1000 * sr // hop_length
delta = float(DELTA)

if __name__ == "__main__":

    input_device = int(input("input device number: "))
    output_device = int(input("output device number: "))
    sd.default.device = [input_device, output_device]

    print("input device: ", sd.query_devices(kind="input")["name"], "\n")
    print("output device: ", sd.query_devices(kind="output")["name"], "\n")

    debug = False
    # debug = True
    if debug:
        HOST = "192.168.0.25"
    else:
        HOST = "192.168.0.20"
    LOCAL_HOST = "192.168.0.25"
    PORT = 50003
    PORT2 = 50005

    for i in range(100):
        scene_code = utilities.receive_unity_instruction(LOCAL_HOST, PORT)
        
        if scene_code == '0010':
            print("Pitch Scene Start ---")
        
            duration = 3
            
            data = np.zeros(int(44100), dtype=np.float32)
            shift_size = 1136
            sr = 44100
        
            chord_list = Asus4onE_chord_list.copy()
            before_pitch_name = "null"
        
            while len(chord_list) != 0:
                with sd.InputStream(
                        channels=1,
                        dtype='float32',
                        callback=function1.callback_pitch
                    ):
                    sd.sleep(int(duration * 1000))

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            end_code = "0000"
            sock.sendto(end_code.encode('utf-8'), (HOST, PORT))
            print("send 0000")
            sock.close()
            
        elif scene_code == '0001':
            print("Lesson Scene Start ---")
            duration = 18
            
            data = np.zeros(int(sr)*data_length, dtype=np.float32)
            full_data = np.zeros(int(sr)*duration, dtype=np.float32)
            onset_frames = []
            detected_onset_times = []

            with sd.InputStream(
                        samplerate=sr,
                        channels=1,
                        dtype='float32',
                        callback=function2.callback_rythm
                    ):
                    start_time = ti.time()
                    sd.sleep(int(duration * 1000))
                    print(ti.time() - start_time)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(str(0000).encode('utf-8'), (HOST, PORT))
            
            detected_num = [int((detected_onset_time * sr) + frame_length) for detected_onset_time in detected_onset_times]
            cliped_datas = function2.create_array(full_data, expected_note_points)
            
            fig = plt.figure(figsize=(50, 5))
            ax = fig.add_subplot(111)
            
            ax.plot(full_data, label='onset envelope')
            ax.vlines(detected_num, 0, 1, color='r', linestyle='--', label='onsets')
            plt.show()
            
            good_num = 0
            normal_num = 0
            bad_num = 0

            for dst in cliped_datas:
                result = function2.predict_performances(dst, model)
                print(result)
                utilities.send_data_to_server(HOST, PORT, result)
                recive = utilities.recive_data_from_server(PORT2)
                print(f"Received message: {recive}")
                
        else:
            print("error")

        print("------------")
        print(i)
        print("------------")
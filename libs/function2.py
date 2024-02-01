def calculate_melsp(x, n_fft=1024, hop_length=128):
    stft = np.abs(librosa.stft(x, n_fft=n_fft, hop_length=hop_length))**2
    log_sftf = librosa.power_to_db(stft)
    melsp = librosa.feature.melspectrogram(S=log_sftf, n_mels=128)
    return melsp

def min_max_normalize(x, axis=None):
    min = x.min(axis=axis, keepdims=True)
    max = x.max(axis=axis, keepdims=True)
    result = (x-min)/(max-min)
    return result

def onset_detection(y, sr, rate, frame_length, hop_length, params):
    rms = librosa.feature.rms(y=y*rate, frame_length=frame_length, hop_length=hop_length, center=False)
    onset_envelope = rms[0, 1:] - rms[0, :-1]
    onset_envelope = np.maximum(0.0, onset_envelope)
    onset_frames = librosa.util.peak_pick(onset_envelope, pre_max=params["pre_max"], post_max=params["post_max"], pre_avg=params["pre_avg"], post_avg=params["post_avg"], delta=params["delta"], wait=params["wait"])
    times = librosa.times_like(onset_envelope, sr=sr, hop_length=hop_length)
    return onset_envelope, onset_frames, times

def create_array(full_data, detected_num):
    window_size = 22050
    front_padding = 22050
    back_padding = 44100
    result = []

    for i in detected_num:
        start = max(0, i - front_padding)
        end = min(len(full_data), i + back_padding)

        if end - start < front_padding + back_padding:
            # Padding if the window size is not fully covered
            padding_start = max(0, front_padding - i)
            padding_end = max(0, back_padding - (len(full_data) - i))
            cliped_data = np.pad(full_data[start:end], (padding_start, padding_end), mode='constant')
        else:
            cliped_data = full_data[start:end]

        result.append(cliped_data)

    return np.array(result)

def predict_performances(y, model):
    x = y.reshape(len(y))
    melsp = calculate_melsp(x)
    
    pred = model.predict(melsp.reshape(1, 128, 517, 1))
    result = ""
    for i in range(1, 6):
        result += str(np.argmax(pred[6-i])) + ","
        
    result += str(np.argmax(pred[0]))
    
    return result

def callback_rythm(indata, frames, time, status):
    global data, onset_frames, non_negative_data, start_time, full_data
    data = np.roll(data, -shift_size, axis=0)
    data[-shift_size:] = indata.reshape((shift_size,))
    full_data = np.roll(full_data, -shift_size, axis=0)
    full_data[-shift_size:] = indata.reshape((shift_size,))

    src = data.reshape(data.size) * 100
    rms = librosa.feature.rms(y=src, frame_length=frame_length, hop_length=hop_length, center=False)
    onset_envelope = rms[0, 1:] - rms[0, :-1]
    onset_envelope = np.maximum(0.0, onset_envelope)
    onset_frames = librosa.util.peak_pick(onset_envelope, pre_max=pre_max, post_max=post_max, pre_avg=pre_avg, post_avg=post_avg, delta=delta, wait=wait)

    if len(onset_frames) != 0:
        _times = librosa.times_like(onset_envelope, sr=sr, hop_length=hop_length)
        for onset_frame in onset_frames:
            elapsed_time = (ti.time() - start_time) - (data_length - _times[onset_frame])
            
            if any(abs(elapsed_time - t) < 1.0 for t in detected_onset_times):
                continue
                
            detected_onset_times.append(elapsed_time)
            
            print(f"detect onset: {elapsed_time}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(str(elapsed_time).encode('utf-8'), (HOST, PORT))
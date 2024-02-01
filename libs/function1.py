def find_nearest(array, value):
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx - 1]) < math.fabs(value - array[idx])):
        return array[idx - 1]
    else:
        return array[idx]


def callback_pitch(indata, frames, time, status):
    global data, chord_list, before_pitch_name
    
    data = np.roll(data, -shift_size, axis=0)
    data[-shift_size:] = indata.reshape((shift_size,))

    rms = np.sqrt(np.mean(indata**2))
    db = 20 * math.log10(rms)

    if db >= -50:
        
        _f0 = librosa.yin(y=data, sr=sr, fmin=60, fmax=440)
        _f0 = [find_nearest(hz_array, i) for i in list(_f0)]
        latest_notes_list = []

        for i in _f0:
            latest_notes_list.append(float(i))

        max_note = max(latest_notes_list, key=latest_notes_list.count)
        pitch_name = hz_notename[max_note]

        if before_pitch_name != pitch_name:
            before_pitch_name = pitch_name
            if len(chord_list) == 0:
                pass
            else:
                if pitch_name == chord_list[0]:
                    del chord_list[0]
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.sendto(str(1111).encode('utf-8'), (HOST, PORT))
                    sock.close()
                    print(pitch_name)
                    print(datetime.datetime.now().isoformat())
                else:
                    pass
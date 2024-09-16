import numpy as np
import sounddevice as sd
import soundfile as sf

with sf.SoundFile('aiueo.wav') as f:
    fs = np.empty(0, dtype=np.float32)

    for i in range(1000000):
        # 8192bits 为一个元音的大致长度 这个长度与采样率有关
        data = f.read(4096, dtype=np.float32)
        if not len(data):
            print(i)
            break
        fs = np.append(fs, data)


    with sf.write(data=fs, samplerate=f.samplerate) as ssf:

        with sd.OutputStream(samplerate=ssf.samplerate,
                             blocksize=8192,
                             channels=ssf.channels,
                             dtype=np.float32) as stream:
            while True:
                data = f.read(4096, dtype=np.float32)
                if not len(data):
                    print(i)
                    break
                stream.write(data)

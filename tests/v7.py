import soundfile as sf
import numpy as np
import time
from src.pymouth import AudioAnalyser


def callback(y, data):
    print(y)


def finished_callback():
    print("finished_callback")


def test1():
    with sf.SoundFile('zh.wav') as f:
        fs = np.empty(0, dtype=np.float32)
        for _ in range(1000000):
            data = f.read(2048, dtype=np.float32)
            if not len(data):
                break
            fs = np.append(fs, data)

        print(fs.dtype)
        print(fs.shape)

        with AudioAnalyser(fs, f.samplerate, channels=1, callback=callback) as a:
            a.sync_action()
            print("end")
            time.sleep(1000000)


def test2():
    with AudioAnalyser('zh.wav', 44100, channels=1, callback=callback) as a:
        a.async_action()
        print("end")
        time.sleep(1000000)


def main():
    test1()


if __name__ == '__main__':
    main()

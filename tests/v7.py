import soundfile as sf
import numpy as np
import time
from src.pymouth import DBAnalyser


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

        with DBAnalyser(fs, f.samplerate, output_channels=1, callback=callback) as a:
            a.sync_action()
            print("end")
            time.sleep(1000000)


def test2():
    with DBAnalyser('zh.wav', 44100, output_channels=1, callback=callback) as a:
        a.async_action()
        print("end")
        time.sleep(1000000)


def main():
    test1()


if __name__ == '__main__':
    main()

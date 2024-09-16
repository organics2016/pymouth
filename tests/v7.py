import time

import numpy as np
import soundfile as sf

from src.pymouth import DBAnalyser


def callback(y, data):
    print(y)


def finished_callback():
    print("finished_callback")


def test1():
    with sf.SoundFile('aiueo.wav') as f:
        fs = None
        for _ in range(1000000):
            data = f.read(2048, dtype=np.float32)
            if not len(data):
                break

            if fs is None:
                fs = np.array(data, dtype=np.float32)
                print(data.shape)
            else:
                fs = np.append(fs, data, axis=0)

        # print(f.samplerate)
        # print(f.channels)
        print(fs.dtype)
        print(fs.shape)
        print(fs.ndim)

        # with DBAnalyser(fs, 44100, 4, callback=callback) as a:
        #     a.sync_action()
        #     print("end")
        #     time.sleep(1000000)


def test2():
    with DBAnalyser('zh.wav', 44100, 4, callback=callback) as a:
        a.async_action()
        print("end")
        time.sleep(1000000)


def main():
    test1()


if __name__ == '__main__':
    main()

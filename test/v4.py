import sounddevice as sd
import soundfile as sf
import queue
import numpy as np

duration = 35  # seconds

buffersize = 1024
blocksize = 2048
samplerate = 44100

q = queue.Queue(maxsize=buffersize)


def callback(outdata, frames, time, status):
    assert frames == blocksize
    if status.output_underflow:
        raise sd.CallbackAbort('Output underflow: increase blocksize?')
    assert not status
    single_channel = outdata.ndim == 1
    try:
        data = q.get_nowait()
    except queue.Empty as e:
        raise sd.CallbackAbort('Buffer is empty: increase buffersize?') from e
    if len(data) < len(outdata):
        if single_channel:
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
        else:
            outdata[:len(data), 0] = data
            outdata[len(data):, 0].fill(0)
        raise sd.CallbackStop
    else:
        if single_channel:
            outdata[:] = data
        else:
            outdata[:, 0] = data


with sf.SoundFile('zh.wav') as f:
    for _ in range(buffersize):
        data = f.read(blocksize, dtype=np.float32)
        print(data)
        print(len(data))
        if not len(data):
            break
        q.put_nowait(data)  # Pre-fill queue
    stream = sd.OutputStream(
        samplerate=samplerate, blocksize=blocksize,
        channels=1, dtype=np.float32,
        callback=callback)

    with stream:
        sd.sleep(int(duration * 1000))
        # timeout = blocksize * buffersize / f.samplerate
        # print(timeout)
        # while 1:
        #     data = f.read(blocksize)
        #     q.put(data, timeout=timeout)
    # event.wait()  # Wait until playback is finished

# with sd.Stream(channels=2, callback=callback):
#     sd.sleep(int(duration * 1000))

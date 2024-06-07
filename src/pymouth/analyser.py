import librosa
import soundfile as sf
import numpy as np
import sounddevice as sd
from threading import Thread


class AudioAnalyser:
    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float,
                 channels: int,
                 callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 2048,
                 buffer_size: int = 20):

        self.buffer_size = buffer_size
        self.block_size = block_size
        self.dtype = dtype
        self.auto_play = auto_play
        self.audio = audio
        self.samplerate = samplerate
        self.channels = channels
        self.callback = callback
        self.thread = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
        # self.close()

    def async_action(self):
        self.thread = Thread(target=self.sync_action)
        self.thread.start()

    def sync_action(self):

        if self.auto_play:
            with sd.OutputStream(samplerate=self.samplerate,
                                 blocksize=self.block_size,
                                 channels=self.channels,
                                 dtype=self.dtype) as stream:

                if isinstance(self.audio, np.ndarray):
                    datas = split_list_by_n(self.audio, self.block_size)
                    for data in datas:
                        print(len(data))
                        self.call(data, stream)
                elif isinstance(self.audio, str):
                    with sf.SoundFile(self.audio) as f:
                        while True:
                            data = f.read(self.block_size, dtype=self.dtype)
                            print(len(data))
                            if not len(data):
                                break
                            self.call(data, stream)
                elif isinstance(self.audio, sf.SoundFile):
                    while True:
                        data = self.audio.read(self.block_size, dtype=self.dtype)
                        print(len(data))
                        if not len(data):
                            break
                        self.call(data, stream)

        else:
            if isinstance(self.audio, np.ndarray):
                datas = split_list_by_n(self.audio, self.block_size)
                for data in datas:
                    self.call(data)

            elif isinstance(self.audio, str):
                with sf.SoundFile(self.audio) as f:
                    while True:
                        data = f.read(self.block_size, dtype=self.dtype)
                        if not len(data):
                            break
                        self.call(data)

            elif isinstance(self.audio, sf.SoundFile):
                while True:
                    data = self.audio.read(self.block_size, dtype=self.dtype)
                    if not len(data):
                        break
                    self.call(data)

    def call(self, data: np.ndarray, stream: sd.OutputStream = None):
        if stream is not None:
            stream.write(data)
        self.callback(audio2db2(data), data)


def audio2db2(audio_data: np.ndarray, sample_size: int = 60) -> float:
    audio_data = channel_conversion(audio_data)
    # 计算频谱图
    spectrogram = librosa.stft(audio_data)
    # print(spectrogram[0])
    # 将幅度转换为分贝
    spectrogram_db = librosa.amplitude_to_db((np.abs(spectrogram)) ** 2)

    # 采样
    spectrogram_db = spectrogram_db[0:len(audio_data):sample_size]
    # 采样出nan值统一为 最小分贝
    spectrogram_db = np.nan_to_num(spectrogram_db, nan=-100.0)
    # 标准化
    min = -100
    max = np.max(spectrogram_db)
    sub = max - min
    if sub == 0:
        return 0.0

    mean = spectrogram_db.mean()
    y = (mean - min) / sub
    # print(y)
    return y


def channel_conversion(audio: np.ndarray):
    # 如果音频数据为立体声，则将其转换为单声道
    if audio.ndim == 2 and audio.shape[1] == 2:
        return audio[:, 0]
    return audio


def split_list_by_n(list_collection, n):
    """
    将集合均分，每份n个元素
    :param list_collection:
    :param n:
    :return:返回的结果为评分后的每份可迭代对象
    """
    for i in range(0, len(list_collection), n):
        yield list_collection[i: i + n]

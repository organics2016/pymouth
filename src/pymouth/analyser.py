import librosa
import soundfile as sf
import numpy as np
import sounddevice as sd
import random
from threading import Thread
from abc import ABCMeta, abstractmethod


class Analyser(metaclass=ABCMeta):
    pass


class DBAnalyser(Analyser):
    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float,
                 output_channels: int,
                 callback,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 2048,
                 buffer_size: int = 20,
                 frequency_reduction_probability: float = 0.25):

        self.audio = audio
        self.samplerate = samplerate
        self.output_channels = output_channels
        self.callback = callback
        self.auto_play = auto_play
        self.dtype = dtype
        self.block_size = block_size
        self.buffer_size = buffer_size
        self.frequency_reduction_probability = frequency_reduction_probability
        self.thread = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def async_action(self):
        self.thread = Thread(target=self.sync_action)
        self.thread.start()

    def sync_action(self):

        if self.auto_play:
            with sd.OutputStream(samplerate=self.samplerate,
                                 blocksize=self.block_size,
                                 channels=self.output_channels,
                                 dtype=self.dtype) as stream:

                if isinstance(self.audio, np.ndarray):
                    datas = split_list_by_n(self.audio, self.block_size)
                    for data in datas:
                        self.__call(data, stream)
                elif isinstance(self.audio, str):
                    with sf.SoundFile(self.audio) as f:
                        while True:
                            data = f.read(self.block_size, dtype=self.dtype)
                            if not len(data):
                                break
                            self.__call(data, stream)
                elif isinstance(self.audio, sf.SoundFile):
                    while True:
                        data = self.audio.read(self.block_size, dtype=self.dtype)
                        if not len(data):
                            break
                        self.__call(data, stream)

        else:
            if isinstance(self.audio, np.ndarray):
                datas = split_list_by_n(self.audio, self.block_size)
                for data in datas:
                    self.__call(data)

            elif isinstance(self.audio, str):
                with sf.SoundFile(self.audio) as f:
                    while True:
                        data = f.read(self.block_size, dtype=self.dtype)
                        if not len(data):
                            break
                        self.__call(data)

            elif isinstance(self.audio, sf.SoundFile):
                while True:
                    data = self.audio.read(self.block_size, dtype=self.dtype)
                    if not len(data):
                        break
                    self.__call(data)

    def __call(self, data: np.ndarray, stream: sd.OutputStream = None):
        if stream is not None:
            stream.write(data)
        self.callback(audio2db(data, self.frequency_reduction_probability), data)


def audio2db(audio_data: np.ndarray, frequency_reduction_probability) -> float:
    audio_data = channel_conversion(audio_data)
    # 计算频谱图
    spectrogram = librosa.stft(audio_data)
    # 将幅度转换为分贝
    spectrogram_db = librosa.amplitude_to_db((np.abs(spectrogram)))
    # 采样
    # spectrogram_db = spectrogram_db[0:len(audio_data):sample_size]
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

    # 一定概率降频,可以使音频块之间的分贝浮动增大
    if random.random() < frequency_reduction_probability:
        return y / 2
    # print(y)
    return y


def audio2vowel():
    pass
    # TODO 通过共振峰获取元音
    # sss = librosa.db_to_power(spectrogram_db)
    # print(np.max(sss))


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

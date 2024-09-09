from abc import ABCMeta
from threading import Thread

import librosa
import numpy as np
import sounddevice as sd
import soundfile as sf


class Analyser(metaclass=ABCMeta):
    pass


class DBAnalyser(Analyser):
    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float,
                 output_channels: int,
                 callback,
                 finished_callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 1024):

        self.audio = audio
        self.samplerate = samplerate
        self.output_channels = output_channels
        self.callback = callback
        self.finished_callback = finished_callback
        self.auto_play = auto_play
        self.dtype = dtype
        self.block_size = block_size
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

        if self.finished_callback is not None:
            self.finished_callback()

    def __call(self, data: np.ndarray, stream: sd.OutputStream = None):
        if stream is not None:
            stream.write(data)
        self.callback(audio2db(data), data)


def audio2db(audio_data: np.ndarray) -> float:
    audio_data = channel_conversion(audio_data)
    # 计算频谱
    n_fft = 512 if audio_data.size >= 512 else audio_data.size
    spectrum = librosa.stft(audio_data, n_fft=n_fft)
    # 将频谱转换为分贝
    spectrum_db = librosa.amplitude_to_db((np.abs(spectrum)))
    # 采样
    # spectrum_db = spectrum_db[0:len(audio_data):100]

    # 采样出nan值统一为 最小分贝
    spectrum_db = np.nan_to_num(spectrum_db, nan=-100.0)

    # 标准化
    mean = spectrum_db.mean()
    std = spectrum_db.std()
    # print(f"mean: {mean}, std: {std}")
    if mean == 0 or std == 0:
        return 0

    # y = (std-min)/(max-min) 这里假设: 最小标准差为0,最大标准差是分贝平均值的绝对值, 然后对标准差y进行min-max标准化
    y = float(std / np.abs(mean))
    # print(y)
    # 有标准差大于平均值的情况,
    if y > 1:
        return 1.0
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

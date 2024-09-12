from abc import ABCMeta
from threading import Thread

import librosa
import numpy as np
import sounddevice as sd
import soundfile as sf
from dtw import dtw


class Analyser(metaclass=ABCMeta):
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
                        self.call_adapter(data, stream)

                elif isinstance(self.audio, str):
                    with sf.SoundFile(self.audio) as f:
                        while True:
                            data = f.read(self.block_size, dtype=self.dtype)
                            if not len(data):
                                break
                            self.call_adapter(data, stream)

                elif isinstance(self.audio, sf.SoundFile):
                    while True:
                        data = self.audio.read(self.block_size, dtype=self.dtype)
                        if not len(data):
                            break
                        self.call_adapter(data, stream)

        else:
            if isinstance(self.audio, np.ndarray):
                datas = split_list_by_n(self.audio, self.block_size)
                for data in datas:
                    self.call_adapter(data)

            elif isinstance(self.audio, str):
                with sf.SoundFile(self.audio) as f:
                    while True:
                        data = f.read(self.block_size, dtype=self.dtype)
                        if not len(data):
                            break
                        self.call_adapter(data)

            elif isinstance(self.audio, sf.SoundFile):
                while True:
                    data = self.audio.read(self.block_size, dtype=self.dtype)
                    if not len(data):
                        break
                    self.call_adapter(data)

        if self.finished_callback is not None:
            self.finished_callback()

    def call_adapter(self, data: np.ndarray, stream: sd.OutputStream = None):
        pass


class DBAnalyser(Analyser):
    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float, output_channels: int,
                 callback,
                 finished_callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 1024):
        super().__init__(audio, samplerate, output_channels, callback, finished_callback, auto_play, dtype, block_size)

    def call_adapter(self, data: np.ndarray, stream: sd.OutputStream = None):
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


class VowelAnalyser(Analyser):
    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float,
                 output_channels: int,
                 callback,
                 finished_callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 4096):
        super().__init__(audio, samplerate, output_channels, callback, finished_callback, auto_play, dtype, block_size)

    def call_adapter(self, data: np.ndarray, stream: sd.OutputStream = None):
        if stream is not None:
            stream.write(data)
        self.callback(audio2vowel(data), data)


V_A = [[215.9829, -26.526842], [217.84839, -23.994688]]
V_I = [[170.0406, -75.1104], [160.85315, -81.786285]]
V_U = [[200.94102, -66.91193], [194.62955, -64.79806]]
V_E = [[193.6798, -38.11208], [192.08456, -24.153627]]
V_O = [[209.67409, 0.3272565], [207.94513, 5.8133316]]
V_Silence = [[50.040688, 15.370534], [61.82225, 18.227924]]


def audio2vowel(audio_data: np.ndarray) -> dict[str, float]:
    audio_data = channel_conversion(audio_data)

    # TODO 这里可能要做人声滤波
    # 对线性声谱图应用mel滤波器后，取log，得到log梅尔声谱图，然后对log滤波能量（log梅尔声谱）做DCT离散余弦变换（傅里叶变换的一种），然后保留第2到第13个系数，得到的这12个系数就是MFCC
    mfccs = librosa.feature.mfcc(y=audio_data, sr=22050, n_fft=512, dct_type=1, n_mfcc=3)[1:].T

    if mfccs.shape[0] < 5:
        return {
            'VoiceSilence': 1,
            'VoiceA': 0,
            'VoiceI': 0,
            'VoiceU': 0,
            'VoiceE': 0,
            'VoiceO': 0,
        }

    si = 1 / dtw(V_Silence, mfccs, distance_only=True).normalizedDistance
    a = 1 / dtw(V_A, mfccs, distance_only=True).normalizedDistance
    i = 1 / dtw(V_I, mfccs, distance_only=True).normalizedDistance
    u = 1 / dtw(V_U, mfccs, distance_only=True).normalizedDistance
    e = 1 / dtw(V_E, mfccs, distance_only=True).normalizedDistance
    o = 1 / dtw(V_O, mfccs, distance_only=True).normalizedDistance

    sum = si + a + i + u + e + o

    si_r = si / sum
    a_r = a / sum
    i_r = i / sum
    u_r = u / sum
    e_r = e / sum
    o_r = o / sum

    max = np.max([si_r, a_r, i_r, u_r, e_r, o_r])

    res = {
        'VoiceSilence': 1 if si_r == max else 0,
        'VoiceA': a_r * 2 if a_r == max else a_r,
        'VoiceI': i_r * 2 if i_r == max else i_r,
        'VoiceU': u_r * 2 if u_r == max else u_r,
        'VoiceE': e_r * 2 if e_r == max else e_r,
        'VoiceO': o_r * 2 if o_r == max else o_r,
    }

    if si_r == max:
        # print("VoiceSilence")
        pass
    elif a_r == max:
        print("A")
        print(mfccs)
        print(res)
    elif i_r == max:
        print("I")
        print(mfccs)
        print(res)
    elif u_r == max:
        print("U")
        print(mfccs)
        print(res)
    elif e_r == max:
        print("E")
        print(mfccs)
        print(res)
    elif o_r == max:
        print("O")
        print(mfccs)
        print(res)

    return res


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

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
                 output_device: int,
                 callback,
                 finished_callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 1024):

        self.audio = audio
        self.samplerate = samplerate
        self.output_device = output_device
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

        stream = None
        try:
            if isinstance(self.audio, np.ndarray):
                # 声道验证
                if self.audio.ndim <= 0 or self.audio.ndim > 2:
                    raise ValueError('Audio channel verification failed. Only single or dual channels are supported.')

                stream = sd.OutputStream(samplerate=self.samplerate,
                                         blocksize=self.block_size,
                                         device=self.output_device,
                                         channels=self.audio.ndim,  # if data.shape[1] != channels:
                                         dtype=self.dtype).__enter__() if self.auto_play else None

                datas = split_list_by_n(self.audio, self.block_size)
                for data in datas:
                    self.process(data, stream)

            elif isinstance(self.audio, str):
                with sf.SoundFile(self.audio) as f:
                    stream = sd.OutputStream(samplerate=f.samplerate,
                                             blocksize=self.block_size,
                                             device=self.output_device,
                                             channels=f.channels,
                                             dtype=self.dtype).__enter__() if self.auto_play else None
                    while True:
                        data = f.read(self.block_size, dtype=self.dtype)
                        if not len(data):
                            break
                        self.process(data, stream)

            elif isinstance(self.audio, sf.SoundFile):
                stream = sd.OutputStream(samplerate=self.audio.samplerate,
                                         blocksize=self.block_size,
                                         device=self.output_device,
                                         channels=self.audio.channels,
                                         dtype=self.dtype).__enter__() if self.auto_play else None

                while True:
                    data = self.audio.read(self.block_size, dtype=self.dtype)
                    if not len(data):
                        break
                    self.process(data, stream)

        finally:
            if stream is not None:
                stream.__exit__()

            if self.finished_callback is not None:
                self.finished_callback()

    def process(self, data: np.ndarray, stream: sd.OutputStream):
        if stream is not None:
            stream.write(data)
        self.call_adapter(data)

    def call_adapter(self, data: np.ndarray):
        pass


class DBAnalyser(Analyser):
    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float,
                 output_device: int,
                 callback,
                 finished_callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 2048):
        super().__init__(audio, samplerate, output_device, callback, finished_callback, auto_play,
                         dtype, block_size)

    def call_adapter(self, data: np.ndarray, stream: sd.OutputStream = None):
        self.callback(self.__audio2db(data), data)

    def __audio2db(self, audio_data: np.ndarray) -> float:
        audio_data = channel_conversion(audio_data)
        # 计算频谱
        n_fft = 512 if audio_data.size >= 512 else audio_data.size
        spectrum = librosa.stft(audio_data, n_fft=n_fft)
        # 将频谱转换为分贝
        spectrum_db = librosa.amplitude_to_db((np.abs(spectrum)))
        # 采样
        # spectrum_db = spectrum_db[0:len(audio_data):100]

        # 采样出nan值统一为 最小分贝
        # spectrum_db = np.nan_to_num(spectrum_db, nan=-100.0)

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
    V_A = [[215.9829, -26.526842], [217.84839, -23.994688]]
    V_I = [[170.0406, -75.1104], [160.85315, -81.786285]]
    V_U = [[200.94102, -66.91193], [194.62955, -64.79806]]
    V_E = [[193.6798, -38.11208], [192.08456, -24.153627]]
    V_O = [[209.67409, 0.3272565], [207.94513, 5.8133316]]
    V_Silence = [[50.040688, 15.370534], [61.82225, 18.227924]]

    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float,
                 output_device: int,
                 callback,
                 finished_callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 4096,
                 calibration: dict[str, float] = None):
        super().__init__(audio, samplerate, output_device, callback, finished_callback, auto_play,
                         dtype, block_size)
        if calibration is None:
            calibration = {
                'VoiceSilence': 1.0,
                'VoiceA': 0.4,
                'VoiceI': 0.2,
                'VoiceU': 0.1,
                'VoiceE': 0.2,
                'VoiceO': 0.2,
            }

        self.calibration = calibration

    def call_adapter(self, data: np.ndarray, stream: sd.OutputStream = None):
        self.callback(self.__audio2vowel(data), data)

    def __audio2vowel(self, audio_data: np.ndarray) -> dict[str, float]:
        audio_data = channel_conversion(audio_data)

        # TODO 这里可能要做人声滤波
        # 对线性声谱图应用mel滤波器后，取log，得到log梅尔声谱图，然后对log滤波能量（log梅尔声谱）做DCT离散余弦变换（傅里叶变换的一种），然后保留第2到第13个系数，得到的这12个系数就是MFCC
        mfccs = librosa.feature.mfcc(y=audio_data, sr=22050, n_fft=512, dct_type=1, n_mfcc=3)[1:].T

        # print(mfccs.shape)
        # 过短的音频会导致无法比较，直接按无声处理
        if mfccs.shape[0] < 5:
            return {
                'VoiceSilence': 1,
                'VoiceA': 0,
                'VoiceI': 0,
                'VoiceU': 0,
                'VoiceE': 0,
                'VoiceO': 0,
            }

        si = 1 / dtw(self.V_Silence, mfccs, distance_only=True).normalizedDistance
        a = 1 / dtw(self.V_A, mfccs, distance_only=True).normalizedDistance
        i = 1 / dtw(self.V_I, mfccs, distance_only=True).normalizedDistance
        u = 1 / dtw(self.V_U, mfccs, distance_only=True).normalizedDistance
        e = 1 / dtw(self.V_E, mfccs, distance_only=True).normalizedDistance
        o = 1 / dtw(self.V_O, mfccs, distance_only=True).normalizedDistance

        sum = si + a + i + u + e + o

        si_r = si / sum
        a_r = a / sum
        i_r = i / sum
        u_r = u / sum
        e_r = e / sum
        o_r = o / sum

        max = np.max([si_r, a_r, i_r, u_r, e_r, o_r])

        # TODO 这里可以加一个激活函数过滤噪音 
        res = {
            'VoiceSilence': 1 if si_r == max else 0,
            'VoiceA': a_r + self.calibration['VoiceA'] if a_r == max else 0,
            'VoiceI': i_r + self.calibration['VoiceI'] if i_r == max else 0,
            'VoiceU': u_r + self.calibration['VoiceU'] if u_r == max else 0,
            'VoiceE': e_r + self.calibration['VoiceE'] if e_r == max else 0,
            'VoiceO': o_r + self.calibration['VoiceO'] if o_r == max else 0,
        }

        # if si_r == max:
        #     # print("VoiceSilence")
        #     pass
        # elif a_r == max:
        #     print("A")
        #     print(mfccs)
        #     print(res)
        # elif i_r == max:
        #     print("I")
        #     print(mfccs)
        #     print(res)
        # elif u_r == max:
        #     print("U")
        #     print(mfccs)
        #     print(res)
        # elif e_r == max:
        #     print("E")
        #     print(mfccs)
        #     print(res)
        # elif o_r == max:
        #     print("O")
        #     print(mfccs)
        #     print(res)

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

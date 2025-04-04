import traceback
from abc import ABCMeta
from concurrent.futures import ThreadPoolExecutor

import librosa
import numpy as np
import sounddevice as sd
import soundfile as sf
from dtw import dtw


class Analyser(metaclass=ABCMeta):
    V_A = [[157.28203, -18.084631],
           [184.55794, -70.21922],
           [180.11708, -69.37925],
           [186.3136, -68.28505],
           [184.01038, -62.837513],
           [181.70918, -56.22454],
           [183.93184, -55.787033],
           [177.58957, -55.56417],
           [210.36815, -42.245583]]
    V_I = [[154.23402, - 66.638794],
           [109.41006, -76.42681],
           [104.646484, -79.092224],
           [100.69435, -73.16504],
           [106.442406, -68.50664],
           [104.717026, -67.13239],
           [98.70581, -67.052155],
           [90.54036, -64.939255],
           [96.68744, -4.7852263]]
    V_U = [[177.38, -21.598547],
           [163.56247, -60.48896],
           [162.29306, -65.40919],
           [147.10324, -77.276535],
           [145.81586, -81.49585],
           [141.00285, -80.76966],
           [137.3823, -83.69654],
           [125.162674, -86.36088],
           [182.829, -57.803486]]
    V_E = [[45.139225, -3.552611],
           [82.19922, -65.22143],
           [154.64558, -90.886116],
           [153.86205, -97.447235],
           [158.62253, -77.25729],
           [155.23709, -56.107735],
           [149.8651, -64.127594],
           [145.0244, -55.381966],
           [175.49411, -33.858017]]
    V_O = [[224.24329, -10.556553],
           [193.64792, -22.315527],
           [186.96034, -20.628428],
           [184.96133, -16.40874],
           [186.04208, -22.023905],
           [185.25256, -11.928689],
           [185.24428, -5.041305],
           [181.70624, -3.2469425],
           [131.43114, 3.3550904]]
    V_Silence = [[52.750603, -4.9177713],
                 [84.026146, 21.443743],
                 [77.42841, 2.3937027],
                 [85.50844, 21.711079],
                 [80.75325, 7.308112],
                 [82.622925, 16.251738],
                 [69.67996, 10.19037],
                 [80.5309, 6.884417],
                 [71.37026, 22.482405]]

    def __init__(self, temperature: float = 10.0):
        self.executor = ThreadPoolExecutor(1)
        self.temperature = temperature

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def action_noblock(self,
                       audio: np.ndarray | str | sf.SoundFile,
                       samplerate: int | float,
                       output_device: int,
                       callback,
                       finished_callback=None,
                       auto_play: bool = True,
                       dtype: np.dtype = np.float32,
                       block_size: int = 4096):

        self.executor.submit(self.action_block,
                             *(audio,
                               samplerate,
                               output_device,
                               callback,
                               finished_callback,
                               auto_play,
                               dtype,
                               block_size))

    def action_block(self,
                     audio: np.ndarray | str | sf.SoundFile,
                     samplerate: int | float,
                     output_device: int,
                     callback,
                     finished_callback=None,
                     auto_play: bool = True,
                     dtype: np.dtype = np.float32,
                     block_size: int = 4096):

        stream = None
        try:
            if isinstance(audio, np.ndarray):
                # 声道验证
                if audio.ndim <= 0 or audio.ndim > 2:
                    raise ValueError('Audio channel verification failed. Only single or dual channels are supported.')

                stream = sd.OutputStream(samplerate=samplerate,
                                         blocksize=block_size,
                                         device=output_device,
                                         channels=audio.ndim,  # if data.shape[1] != channels:
                                         dtype=dtype).__enter__() if auto_play else None

                datas = split_list_by_n(audio, block_size)
                for data in datas:
                    self.play(callback, data, samplerate, stream)

            elif isinstance(audio, str):
                with sf.SoundFile(audio) as f:
                    stream = sd.OutputStream(samplerate=f.samplerate,
                                             blocksize=block_size,
                                             device=output_device,
                                             channels=f.channels,
                                             dtype=dtype).__enter__() if auto_play else None
                    while True:
                        data = f.read(block_size, dtype=dtype)
                        if not len(data):
                            break
                        self.play(callback, data, samplerate, stream)

            elif isinstance(audio, sf.SoundFile):
                stream = sd.OutputStream(samplerate=audio.samplerate,
                                         blocksize=block_size,
                                         device=output_device,
                                         channels=audio.channels,
                                         dtype=dtype).__enter__() if auto_play else None

                while True:
                    data = audio.read(block_size, dtype=dtype)
                    if not len(data):
                        break
                    self.play(callback, data, samplerate, stream)

        except Exception:
            traceback.print_exc()
        finally:
            if stream is not None:
                stream.__exit__()

            if finished_callback is not None:
                finished_callback()

    def play(self, callback, data: np.ndarray, samplerate: int | float, stream: sd.OutputStream):
        if stream is not None:
            stream.write(data)
        callback(self.process(data, samplerate), data)

    def process(self, data: np.ndarray, samplerate: int | float):
        pass

    def _audio2vowel(self, audio_data: np.ndarray, samplerate: int | float) -> dict[str, float]:
        audio_data = channel_conversion(audio_data)

        # TODO 这里可能要做人声滤波 , 人声分离比较复杂且耗费性能，暂时不提供支持
        # 对线性声谱图应用mel滤波器后，取log，得到log梅尔声谱图，然后对log滤波能量（log梅尔声谱）做DCT离散余弦变换（傅里叶变换的一种），然后保留第2到第13个系数，得到的这12个系数就是MFCC
        n_fft = get_n_fft(audio_data.size, samplerate)
        mfccs = librosa.feature.mfcc(y=audio_data, sr=samplerate, n_fft=n_fft, dct_type=1, n_mfcc=3)[1:].T
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

        # 通过DTW(动态时间规整算法) 计算 当前帧窗与元音帧窗的距离，值越小越相似
        si = dtw(self.V_Silence, mfccs, distance_only=True).normalizedDistance
        a = dtw(self.V_A, mfccs, distance_only=True).normalizedDistance
        i = dtw(self.V_I, mfccs, distance_only=True).normalizedDistance
        u = dtw(self.V_U, mfccs, distance_only=True).normalizedDistance
        e = dtw(self.V_E, mfccs, distance_only=True).normalizedDistance
        o = dtw(self.V_O, mfccs, distance_only=True).normalizedDistance

        # log = f"Silence:{si:f}, A:{a:f}, I:{i:f}, U:{u:f}, E:{e:f}, O:{o:f}"
        # print(log)
        # 对距离取负，值越大越相似，再对相似度进行softmax，取相似度的概率分布。这里 temperature 取大值降低置信度，可以使输出元音的整体概率更平滑，口型更加真实。
        r = np.array([-1 * i for i in [si, a, i, u, e, o]])
        r = softmax(r, temperature=self.temperature).tolist()
        # print([f"{t:f}" for t in r])

        res = {
            'VoiceSilence': r[0],
            'VoiceA': r[1],
            'VoiceI': r[2],
            'VoiceU': r[3],
            'VoiceE': r[4],
            'VoiceO': r[5],
        }

        return res


class DBAnalyser(Analyser):
    def __init__(self, temperature: float = 10.0):
        super().__init__(temperature=temperature)

    def process(self, data: np.ndarray, samplerate: int | float):
        return self._audio2db(data, samplerate)

    def _audio2db(self, audio_data: np.ndarray, samplerate: int | float) -> float:
        res = self._audio2vowel(audio_data, samplerate)
        vs = res['VoiceSilence']
        max = np.max([res[k] for k in res.keys()])
        return max if max != vs else 0


class VowelAnalyser(Analyser):
    def __init__(self, temperature: float = 10.0):
        super().__init__(temperature=temperature)

    def process(self, data: np.ndarray, samplerate: int | float):
        return self._audio2vowel(data, samplerate)


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


n_fft_ref_list = [128, 512, 1024, 2048, 4096]


def get_n_fft(audio_block_size: int, sample_rate: int, milliseconds: int = 23) -> int:
    """
    计算FFT，计算给定时间和采样率内最适合的FFT。
    一般认为每23毫秒左右为发音的一帧，对每一帧做 FFT（快速傅里叶变换），傅里叶变换的作用是把时域信号转为频域信号
    :param audio_block_size:
    :param sample_rate:
    :param milliseconds:
    :return:
    """
    n_fft = sample_rate * (milliseconds / 1000)
    if n_fft > audio_block_size:
        return audio_block_size
    return min(n_fft_ref_list, key=lambda n_fft_ref: abs(n_fft_ref - n_fft))


def softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """
    带温度参数的softmax函数
    temperature > 1：使分布更平滑（降低置信度）
    temperature < 1：使分布更尖锐（提高置信度）
    temperature = 1：标准softmax

    参数:
    x -- 输入向量或矩阵(numpy数组)
    temperature -- 温度参数(正数，默认为1.0)

    返回:
    s -- softmax计算结果(与x形状相同)

    异常:
    ValueError -- 如果温度<=0
    """
    if temperature <= 0:
        raise ValueError("Temperature must be positive")

    # 防止数值溢出，减去最大值
    x = x / temperature
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0, keepdims=True)

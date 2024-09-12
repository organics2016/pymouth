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


V_A = [[145.02333, 26.781, 6.1290774, -26.856123, -41.1231, -39.322346, 3.4086103, 13.219937, -0.69471216, -17.419374,
        -10.380736, -0.33100075],
       [215.9829, -26.526842, 42.837597, -47.90461, 13.49669, -54.671093, 8.720818, 7.4525347, -10.524191, -18.69641,
        -12.307855, 17.688532],
       [217.84839, -23.994688, 38.287548, -61.063766, 8.822869, -53.691948, 8.113499, 4.952387, -6.4489183, -20.413128,
        -16.906914, 16.604895],
       [225.64812, -15.16951, 45.811222, -59.272305, -0.24408786, -48.62799, 9.137029, 1.9766756, -7.2262673,
        -20.037949, -17.762926, 24.618292],
       [219.62877, -13.676692, 44.12559, -59.115643, 11.729919, -49.927605, -5.8388805, 0.684294, 4.6927233, -18.779129,
        -19.386663, 19.17999],
       [212.53362, -8.830178, 46.180103, -74.16676, 5.3295054, -47.068497, -3.7286007, 1.5057967, -3.9033184,
        -20.963476, -14.499702, 19.450336],
       [224.93294, -0.9325334, 47.366253, -72.51535, -0.15856507, -41.687885, 3.184025, 3.9756246, -2.1025705,
        -25.175959, -12.756801, 20.704666],
       [209.76573, -8.131612, 62.050697, -69.75047, 3.48618, -42.64332, 3.5795977, 5.4472356, -7.4328275, -21.548304,
        -13.191207, 17.689106],
       [215.21838, -5.020641, 40.908676, -58.796368, 11.239996, -47.99422, -0.956311, 11.30326, -13.765612, -20.047686,
        -2.7282867, 9.02275]]
V_I = [[160.85315, -81.786285, 33.597267, 47.406963, 54.451965, -19.120838, -18.019691, 16.238123, 27.698627, -4.321855,
        -0.23177141, 15.700897],
       [158.08246, -92.883095, 56.61916, 54.219963, 67.20857, -33.58262, -26.002842, 7.8766904, 20.46634, -23.535753,
        -16.620043, 12.226443],
       [157.65501, -93.97981, 61.79107, 47.716373, 65.24457, -32.18217, -26.059065, 10.881109, 20.306824, -28.071175,
        -12.769851, 9.801632],
       [156.91429, -94.66543, 67.426636, 50.08268, 69.56231, -23.75132, -30.554903, 10.058938, 20.876678, -31.846148,
        -10.627416, 13.470426],
       [157.16214, -89.641495, 64.841835, 46.56773, 73.392044, -28.790758, -23.721785, 12.614285, 15.801821, -31.424377,
        -16.56785, 12.1242695],
       [152.31578, -87.42269, 70.25196, 45.115536, 72.32821, -27.392847, -19.331913, 2.5940425, 12.885904, -25.393295,
        -16.96544, 13.767369],
       [149.03383, -82.11328, 74.12612, 42.756554, 75.0732, -25.94563, -18.961384, 3.7299185, 8.424352, -28.160368,
        -14.287716, 11.282052],
       [146.13559, -82.44648, 75.76993, 42.707195, 79.13331, -24.584505, -18.48941, 4.3194375, 9.771216, -22.811024,
        -16.53929, 6.407611],
       [85.62743, -11.913851, 36.769768, 44.25965, 16.174826, -14.061316, -4.9391685, 10.301868, 9.546341, -5.2362356,
        -7.6843405, -9.991801]]
V_U = [[159.3681, -11.071153, 25.056889, 31.986082, 20.089493, -21.119295, 6.42783, 32.28108, 1.5852615, -30.976116,
        -17.196981, -8.536826],
       [181.9477, -41.721306, 31.821321, 8.634762, 26.998922, -24.320215, -4.2573113, 26.696184, 16.390167, -40.362427,
        -24.165964, -4.4527273],
       [195.78648, -43.559906, 27.259281, -2.9657123, 45.13867, -21.123846, -9.708863, 28.935902, 18.441475, -33.066406,
        -20.920351, 2.4241261],
       [195.57083, -60.17581, 29.521307, -1.7978629, 42.87503, -25.427416, -8.678386, 18.71153, 20.735512, -32.242237,
        -20.88433, 3.7995775],
       [200.94102, -66.91193, 30.37527, -4.4983435, 39.27317, -23.334412, -9.9792595, 24.915977, 24.406574, -35.22114,
        -19.087936, 2.9024248],
       [194.62955, -64.79806, 44.638218, -2.8806593, 36.88669, -24.03339, -9.819003, 28.233055, 27.784304, -37.508236,
        -21.5868, 2.020724],
       [197.79073, -63.343273, 40.5231, -6.893136, 36.646458, -22.157309, -4.2763405, 24.314283, 19.170618, -40.315845,
        -19.141087, 7.0035176],
       [191.43483, -62.644985, 43.48925, -10.72939, 41.34459, -25.300909, -1.1806667, 21.734066, 21.84719, -32.51056,
        -24.470304, 8.288488],
       [190.6217, -54.617844, 46.467857, 7.182294, 39.005276, -17.51997, 19.849905, 24.195904, 17.639019, -28.03202,
        -13.12109, -1.5847856]]
V_E = [[160.9207, -27.831097, 57.80301, -1.627146, 46.42789, -32.11298, 12.057528, -21.545156, -5.332859, -18.83738,
        -13.234362, 4.1502476],
       [186.55655, -38.004097, 48.603085, -7.1258364, 64.84348, -40.94646, 2.1973403, 5.0202613, -8.644367, -15.559499,
        0.5709229, 12.285181],
       [191.04213, -33.88038, 48.37384, -10.74538, 65.38172, -32.752716, 4.3044076, -8.238798, -13.795583, -17.781136,
        -3.4717672, 15.163681],
       [183.0443, -34.952187, 52.631523, -2.7570028, 66.48372, -36.102932, 6.442519, -6.6857133, -14.778542, -19.139387,
        0.60979325, 13.884282],
       [193.6798, -38.11208, 49.188183, -8.41166, 66.34901, -33.282722, 1.1714948, 1.3649179, -12.812608, -24.758348,
        -0.29010287, 18.8924],
       [192.08456, -24.153627, 45.972004, -16.597313, 73.63422, -27.68429, -1.4875942, -11.4918785, -11.193161,
        -16.851048, -5.1285195, 19.10218],
       [183.82236, -21.818422, 58.47491, -3.0812736, 61.882996, -39.45055, 6.260365, -3.2103884, -10.028254, -14.965299,
        -4.9522896, 20.754942],
       [183.12512, -13.902214, 67.01603, -14.875491, 48.900826, -27.715494, 18.539745, -9.981774, -27.025942,
        -20.688854, 6.7024517, 20.428696],
       [126.77478, 18.036097, 40.453663, 17.896889, 11.916333, -3.6141508, 2.6909683, -11.634538, -18.444355,
        -18.157963, 1.0575595, 6.569986]]
V_O = [[207.94832, 8.159289, 62.135036, 16.036856, 7.0481744, -33.983715, -43.567543, -1.4686158, 3.4015703, -36.30147,
        -18.674768, 19.19357],
       [212.5458, 4.696858, 61.375576, 12.88193, 22.491413, -45.929802, -58.485725, -2.4555883, 10.52324, -39.951508,
        -28.125067, 35.76337],
       [209.67409, 0.3272565, 65.672226, 16.198101, 23.182867, -41.77075, -53.82287, -9.4585705, 13.763308, -41.271877,
        -36.27691, 25.16234],
       [207.94513, 5.8133316, 65.55984, 10.071958, 23.34589, -49.54614, -48.762596, -5.119465, 10.977482, -34.801025,
        -40.457626, 35.44803],
       [215.48485, 0.81210476, 62.02086, 19.625292, 19.989035, -41.731792, -50.814514, -6.8180027, 16.30673, -42.73908,
        -34.223763, 31.127996],
       [207.30493, 8.938618, 66.365814, 14.633777, 28.983408, -46.875786, -50.07367, -3.562775, 8.917103, -39.375538,
        -34.534756, 30.52363],
       [207.69054, 20.060589, 64.2886, 10.267557, 29.853779, -45.56677, -50.991764, -3.7722065, 13.741737, -35.37179,
        -36.300755, 31.482716],
       [201.68712, 16.897303, 71.741104, 14.065498, 28.565058, -50.454563, -50.236942, -1.6972095, 9.058221, -36.445683,
        -33.566746, 27.650747],
       [114.01924, 18.622833, 14.09559, 1.4939548, 4.2916374, -0.052627128, -4.9388514, -7.9732084, -3.9760985,
        -5.739645, -2.450868, -2.8737679]]
V_Silence = [
    [31.558979, 0.44244966, 14.549549, 16.45643, 12.431671, 1.6467339, 14.796138, 0.382705, 2.784441, -11.144224,
     4.8579903, -13.0905075],
    [47.13861, 14.30177, 34.957428, 20.92185, 19.754122, 7.293544, 7.0860972, -2.325054, 14.184402, 5.993093, 9.098588,
     -7.239363],
    [48.030754, 26.705408, 35.36986, 13.712203, 17.097208, 7.6618247, 12.784994, 1.6751161, 9.939173, 1.5772204,
     1.5663186, -11.659863],
    [50.040688, 15.370534, 32.713615, 17.151535, 23.933979, 4.276849, 9.114249, -2.9157043, 6.959679, 7.057296,
     7.557073, -1.5247283],
    [61.82225, 18.227924, 21.605844, 7.9443107, 13.930671, 4.258086, 10.407301, 10.852777, 14.000348, 4.9289775,
     0.6498377, -10.033613],
    [52.437267, 21.260025, 17.956087, 10.969496, 21.423378, -0.3563092, 3.917253, -0.77307427, 3.2717118, -6.976213,
     5.930708, -6.2388387],
    [54.082607, 19.824707, 11.748185, -5.0192313, 2.4771514, -2.7374456, 1.7570888, -2.397428, 5.242214, -3.9039183,
     -0.0781019, 2.9796767],
    [55.287575, 8.518954, 17.678425, 11.533352, 13.06441, 7.5875816, 1.0445689, -5.9021535, -5.077315, -4.243451,
     9.637786, 9.865019],
    [45.4169, 11.008699, 15.057445, 3.982493, 3.6514018, -6.529552, -10.568807, -17.660809, 9.68425, 2.602345,
     -3.0008593, -5.456085]]


def audio2vowel(audio_data: np.ndarray) -> dict[str, float]:
    audio_data = channel_conversion(audio_data)

    # 对线性声谱图应用mel滤波器后，取log，得到log梅尔声谱图，然后对log滤波能量（log梅尔声谱）做DCT离散余弦变换（傅里叶变换的一种），然后保留第2到第13个系数，得到的这12个系数就是MFCC
    mfccs = librosa.feature.mfcc(y=audio_data, sr=22050, n_fft=512, dct_type=1, n_mfcc=13)[1:].T

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

    if si_r == max:
        print("VoiceSilence")
    elif a_r == max:
        print("A")
    elif i_r == max:
        print("I")
    elif u_r == max:
        print("U")
    elif e_r == max:
        print("E")
    elif o_r == max:
        print("O")

    res = {
        'VoiceSilence': 1 if si_r == max else 0,
        'VoiceA': a_r * 2 if a_r == max else 0,
        'VoiceI': i_r * 2 if i_r == max else 0,
        'VoiceU': u_r * 2 if u_r == max else 0,
        'VoiceE': e_r * 2 if e_r == max else 0,
        'VoiceO': o_r * 2 if o_r == max else 0,
    }

    # res = {
    #     'VoiceSilence': si_r,
    #     'VoiceA': a_r,
    #     'VoiceI': i_r,
    #     'VoiceU': u_r,
    #     'VoiceE': e_r,
    #     'VoiceO': o_r,
    # }

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

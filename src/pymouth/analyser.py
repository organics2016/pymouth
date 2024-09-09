from abc import ABCMeta
from threading import Thread

import librosa
import numpy as np
import sounddevice as sd
import soundfile as sf
from dtw import dtw


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


class VowelAnalyser(Analyser):
    def __init__(self,
                 audio: np.ndarray | str | sf.SoundFile,
                 samplerate: int | float,
                 output_channels: int,
                 callback,
                 finished_callback=None,
                 auto_play: bool = True,
                 dtype: np.dtype = np.float32,
                 block_size: int = 8192):

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
        self.callback(audio2vowel(data), data)


V_A = [[198.71388, 38.76888, 3.9094877, 0.32292867, 19.950138, -53.741825, -51.379116, -21.977896, 6.6360583, 5.586686,
        -17.53236, -4.3687444],
       [187.66109, 35.62394, 10.863738, 2.2901247, 32.14099, -49.18204, -51.0537, -15.533592, 14.61628, 7.6031327,
        -19.45322, -10.802334],
       [180.62247, 20.448679, 15.239678, -5.9582086, 32.62517, -39.54596, -50.618553, -18.974545, 16.645172, 5.5501547,
        -12.168915, -12.25103],
       [172.59239, 18.298965, 13.313555, -16.512497, 29.280344, -32.435703, -36.806496, -24.205107, 16.046885, 7.327297,
        -9.062161, -14.434003],
       [176.29185, 25.365337, 18.13613, -17.941023, 30.470604, -34.920227, -30.452442, -20.614834, 8.68204, 8.344372,
        -7.273391, -11.673656],
       [183.30385, 33.655807, 30.971558, -20.440784, 27.09118, -34.56416, -31.88251, -20.72051, 4.380729, 11.207425,
        -7.4110985, -10.3197155],
       [186.03636, 45.577496, 33.64668, -30.034832, 23.33628, -29.772722, -36.27347, -22.406502, 4.175247, 13.105899,
        -4.965236, -13.718162],
       [190.73517, 40.226727, 30.414112, -31.135653, 32.021484, -29.386967, -45.81017, -23.979763, 5.451158, 12.413282,
        -1.8298998, -13.706656],
       [196.36205, 41.262447, 33.539978, -39.171772, 40.156242, -30.133457, -49.84323, -27.990866, 8.729948, 10.479958,
        -1.2639568, -13.982801],
       [199.05849, 43.18852, 32.313072, -42.882145, 35.708637, -26.976095, -45.930496, -33.955254, 7.408169, 16.194897,
        -3.4975338, -15.721686],
       [193.62938, 46.939037, 37.283646, -49.997894, 30.670168, -26.690742, -40.9907, -36.588974, 6.758338, 20.310894,
        -2.2859695, -19.638807],
       [196.0363, 48.47691, 39.237934, -53.153847, 29.62034, -25.692816, -37.36647, -41.010418, 10.052166, 27.40341,
        -8.495198, -24.692234],
       [200.7361, 47.65459, 37.272972, -49.43381, 26.923258, -26.753794, -35.97029, -36.91452, 7.1217647, 23.456356,
        -7.170564, -25.922998],
       [196.58673, 48.67662, 43.154274, -44.62198, 21.709572, -30.112087, -39.407368, -30.724297, 8.318672, 12.346386,
        -4.856419, -23.055393],
       [193.59203, 53.696342, 47.298203, -44.105946, 19.166471, -29.377707, -39.74874, -31.123856, 14.416143, 3.8888853,
        -10.0401, -15.652301],
       [191.63547, 51.777657, 47.55266, -37.63127, 16.050724, -35.001297, -37.87399, -31.636068, 11.506292, 0.24466442,
        -6.476188, -10.801451],
       [187.18477, 55.18046, 39.827732, -26.404741, 3.9680793, -39.019333, -31.289352, -26.609823, -0.06280075,
        3.414262, -4.8433237, -7.0397196]]
V_I = [[95.81396, -57.533535, 54.2177, 21.395905, 63.298424, -8.648099, 32.21866, 2.5897334, 1.4486392, 14.304414,
        11.28342, 8.474755],
       [71.07126, -69.04814, 61.433887, 28.762518, 68.26275, -5.6036444, 33.580776, 4.348162, 5.55841, 17.866993,
        17.749855, 11.217096],
       [52.46617, -77.54803, 59.71464, 30.872683, 70.69166, -4.300055, 34.201885, 6.668679, 7.8646564, 23.512121,
        24.346281, 11.163569],
       [44.59776, -76.94457, 64.363144, 32.272404, 74.70921, -6.472059, 31.476398, 6.194023, 5.3421407, 23.128336,
        27.764763, 11.45122],
       [37.861866, -76.2733, 68.72609, 35.039093, 74.01244, -8.566797, 29.573677, 7.1067643, 5.33279, 19.644299,
        28.647312, 10.876282],
       [40.063057, -74.00775, 67.50532, 32.260334, 69.70974, -9.761227, 29.721317, 6.6483674, 6.651391, 19.269283,
        26.393251, 14.54935],
       [45.15125, -71.64863, 64.89178, 27.346046, 71.41203, -11.675172, 25.177782, 5.315433, 7.5899982, 19.788696,
        23.258009, 16.002981],
       [48.51343, -76.54115, 67.52073, 34.585, 73.65259, -7.9198627, 26.174135, 5.9320645, 6.623894, 22.836897,
        25.04844, 13.881896],
       [49.82269, -82.509026, 71.01231, 41.227276, 76.189026, -1.5064435, 30.649454, 7.5833983, 5.006809, 21.572212,
        22.005438, 11.283956],
       [51.109444, -82.88486, 68.438324, 40.92837, 76.99486, 1.3191824, 37.203907, 11.935441, 6.0343323, 19.988705,
        20.040981, 6.751992],
       [59.62937, -79.46998, 65.04351, 35.911785, 72.8742, 3.3073018, 34.418854, 10.070918, 10.07803, 23.058338,
        17.005156, 5.786653],
       [63.927853, -81.62167, 60.783916, 34.375515, 69.517715, 7.9104686, 30.862541, 8.023186, 16.553593, 26.436293,
        11.824693, 12.155954],
       [68.93126, -85.06551, 61.25491, 38.368034, 68.65538, 8.990043, 26.448547, 8.536332, 16.842001, 22.853802,
        12.689985, 12.341377],
       [70.22792, -86.38802, 63.967495, 37.347553, 71.80734, 7.6975756, 26.118464, 5.7538705, 15.394865, 18.949799,
        12.850823, 6.748766],
       [77.63296, -89.37596, 67.649734, 33.770985, 70.672325, 8.507457, 23.92362, 4.135909, 16.29808, 16.928434,
        12.612365, 2.7035902],
       [105.61588, -69.23118, 54.910225, 30.743511, 46.711235, 3.4842288, 12.033815, 3.575228, 7.293895, 13.769682,
        1.7682612, 5.5745506],
       [121.825516, -51.035385, 40.42419, 27.63774, 31.730465, 2.2608016, 8.617754, 2.9919035, 4.9342256, 8.581605,
        -3.7061152, 4.8935614]]
V_U = [
    [144.70337, 28.69964, 53.462673, 5.019077, 15.873339, -4.5011, 13.036841, -2.0985873, 8.588156, 8.479094, 18.806803,
     8.6338005],
    [137.66003, 19.972607, 59.06079, 1.2587707, 27.05349, -6.516466, 17.38527, -6.0873923, 10.448684, 4.5013494,
     24.780697, 10.431901],
    [127.435585, 10.624982, 61.04921, 1.708835, 30.34642, -6.018, 18.364027, -9.345762, 11.66521, 2.5762558, 27.381205,
     13.675796],
    [125.160774, 10.624678, 65.59426, -3.0211585, 28.53629, -4.354963, 18.627804, -11.855909, 11.41874, 4.4910226,
     30.690842, 10.634309],
    [122.00205, 14.588855, 70.917755, -5.027238, 25.70073, -3.5054252, 19.37812, -15.811354, 7.3837323, 8.858318,
     36.25451, 8.085254],
    [122.91919, 16.79226, 70.446144, -1.9462711, 21.464441, -0.40764797, 22.455362, -20.044735, 5.259868, 8.040941,
     37.733593, 5.8191185],
    [120.40494, 20.907442, 69.403046, -3.9342709, 23.238827, 1.1321278, 22.603922, -19.866785, 6.5986385, 9.179512,
     37.552017, 3.696858],
    [119.08023, 22.072227, 71.57163, -7.0876255, 21.263338, 1.13483, 21.64781, -18.061226, 8.458448, 10.4623, 41.9564,
     4.5881705],
    [118.865974, 20.802763, 73.84107, -7.859299, 20.403856, 0.5883201, 24.46599, -17.613298, 8.067697, 12.792332,
     43.838684, 6.3170953],
    [119.55611, 19.342428, 71.97169, -9.0851555, 17.41767, 4.673491, 27.34528, -16.864782, 9.306708, 14.401395,
     41.561104, 3.4871602],
    [117.680984, 17.159222, 69.45009, -6.2362447, 17.187, 2.8296804, 32.992355, -19.389511, 9.559498, 15.777765,
     39.957928, 3.5253227],
    [122.48274, 14.503899, 70.92873, -4.135267, 15.702596, 1.571854, 30.954985, -20.966175, 9.81947, 17.658112,
     43.99088, 6.211754],
    [130.03096, 10.265446, 65.91731, -0.240224, 15.301831, 2.656423, 23.820341, -19.042288, 13.503102, 21.46288,
     44.549088, 9.262602],
    [134.24287, 8.84377, 57.02565, 4.7727003, 19.290817, 3.281207, 23.758059, -18.67515, 16.005585, 22.416016, 37.34617,
     13.336239],
    [145.63951, 12.420833, 47.783382, 8.61477, 21.260632, -2.710637, 21.008976, -8.373049, 16.936945, 18.44926,
     35.585075, 15.029291],
    [136.89493, 25.251698, 37.471336, 14.945672, 12.91277, 4.481583, 13.877414, 3.6380894, 11.692214, 17.945932,
     24.540724, 11.163019],
    [122.96458, 26.73128, 31.213358, 15.059363, 11.141758, 9.3384905, 12.457056, 5.793362, 10.621988, 7.9097323,
     9.292856, 2.5892317]]
V_E = [[134.27364, -1.5763581, 20.994755, -1.1525807, 67.50824, 6.6813354, -0.5591203, -24.946186, 3.856891, -3.6655579,
        -19.438448, -6.1184893],
       [140.04706, -2.938433, 17.753288, -1.2058009, 72.153534, 6.1016445, 5.9109836, -26.259832, 0.26304486, -9.161357,
        -8.482435, -8.340692],
       [141.40456, -13.128823, 22.921223, -3.9618762, 70.22937, 13.18602, 10.887503, -26.84265, -1.7510039, -13.78291,
        0.955951, -12.254398],
       [142.1222, -24.255123, 25.680548, -8.157693, 72.265686, 13.405593, 11.489844, -26.66164, -4.144718, -10.325769,
        -1.4758227, -10.870424],
       [146.55026, -20.461151, 21.936607, -7.5606585, 74.671684, 12.428396, 14.424266, -31.646563, -4.5236883,
        -8.735162, -5.441104, -7.970072],
       [143.0888, -16.0088, 26.716703, -16.646103, 80.28607, 14.970634, 14.758513, -33.620502, -3.2880993, -10.487797,
        -10.688669, -6.6743693],
       [142.57187, -13.230363, 27.849098, -20.267084, 80.234344, 22.65572, 8.821254, -33.011135, -1.3231674, -12.763441,
        -7.4389586, -13.998874],
       [152.60904, -10.629983, 19.644804, -16.97023, 77.20224, 24.871218, 6.22261, -33.008915, 1.3334537, -10.111371,
        -5.5579104, -18.98542],
       [158.74254, -5.292088, 11.026153, -18.353346, 81.76115, 26.409666, 1.4859987, -33.7025, 6.126611, -9.03512,
        -13.5036955, -13.645641],
       [159.67421, -8.657584, 5.0625, -10.903256, 87.522026, 20.75482, -2.302293, -30.340757, 14.4425125, -15.455803,
        -15.908354, -5.3403487],
       [155.10439, -13.24583, 5.735598, -5.8357124, 91.05085, 12.193708, -2.9028594, -23.265682, 13.645661, -21.189327,
        -12.122862, -1.9379336],
       [154.38033, -14.020207, 5.1207027, -4.3227015, 94.45054, 7.536528, -4.559441, -18.809109, 8.417327, -22.297144,
        -14.992266, 0.09320594],
       [157.8434, -9.728736, 0.9524099, -0.43505737, 94.833466, 8.595442, -8.311674, -19.357933, 5.3656898, -24.881575,
        -20.121048, 3.160488],
       [163.40744, -0.6499212, -5.597191, 0.19225982, 87.83717, 2.7123535, -12.735958, -14.4225645, 6.205289, -23.22993,
        -22.39095, 1.6621289],
       [164.16437, 7.170888, -8.791831, 2.3695066, 85.48128, 1.7613758, -5.8622375, -14.139942, 7.672671, -20.366707,
        -23.357248, 4.8686113],
       [154.24965, 4.7779307, -6.6337056, 11.804764, 71.97745, 14.01494, 1.307422, -15.720257, -7.4922247, -9.636951,
        -11.872151, -3.3389757],
       [134.5271, 2.0669413, -0.04925539, 15.565146, 56.315136, 20.824926, -0.7535067, -18.45168, -13.972049,
        -4.1943526, -7.908299, -4.879385]]
V_O = [[158.09975, 39.083973, 78.26102, 11.137149, 34.72421, -7.085859, -4.434535, -22.334951, 6.744912, -7.3277392,
        -9.62201, -19.52958],
       [137.14551, 46.630383, 92.26693, 23.46826, 47.945988, -7.8115077, -6.85224, -32.091766, 11.92436, -8.127431,
        -11.861097, -30.545956],
       [124.7845, 53.710262, 100.676956, 28.880007, 51.19642, -9.014388, -6.6505756, -35.111504, 6.2678323, -3.0645647,
        -8.2535925, -40.986618],
       [129.10358, 49.997013, 109.11099, 29.046001, 50.501087, -9.02904, -12.03332, -33.364143, 1.0666465, -2.0527937,
        -4.1869698, -36.978996],
       [125.98572, 41.343323, 115.77753, 36.922985, 51.193615, -13.514509, -13.515414, -35.384277, 1.1040674,
        -3.0420327, -6.758437, -31.192686],
       [126.07868, 41.44569, 110.384026, 36.187187, 51.407845, -14.058305, -10.088208, -37.921375, 2.681587, -4.4862976,
        -7.3058105, -31.530987],
       [131.87755, 49.692783, 95.40194, 27.78613, 56.011158, -2.9657009, -7.142895, -36.552086, 0.20357355, -6.4367857,
        -7.7511363, -35.509724],
       [137.85234, 47.30331, 88.19951, 23.815258, 62.798683, 0.7781482, -12.556822, -33.578564, 2.1331735, -8.056505,
        -8.727233, -33.442467],
       [139.46982, 43.50524, 90.262634, 31.770973, 60.64598, 1.6938426, -11.466067, -36.80124, 8.851414, -6.61188,
        -14.887589, -31.260426],
       [139.22606, 39.627842, 93.63127, 31.914814, 61.2675, 0.6498695, -12.3482485, -35.807964, 10.167263, -5.215488,
        -14.992633, -30.263502],
       [138.80473, 36.479263, 93.289734, 30.308086, 64.518555, -4.050253, -14.206251, -31.953117, 9.881212, -2.5742815,
        -17.554867, -29.412106],
       [135.00612, 30.113592, 97.725395, 34.53824, 60.631817, -5.371949, -13.920392, -29.876324, 7.316429, 0.26522946,
        -19.464968, -26.484604],
       [129.87921, 29.572227, 105.42673, 38.230263, 53.850986, -3.7464108, -18.152939, -35.39135, 8.299209, -0.96145266,
        -15.505294, -26.551617],
       [123.304344, 29.29951, 114.86665, 40.107384, 56.05654, 2.4799757, -23.666014, -43.81224, 9.838187, -6.4053693,
        -15.6104765, -22.347527],
       [113.60263, 35.336086, 118.187744, 39.491753, 58.781204, -3.8495147, -28.201227, -42.862797, 7.301565,
        -6.8640347, -11.562535, -21.472843],
       [125.28896, 30.538368, 61.939716, 19.36174, 28.076218, 2.6717207, -6.7411447, -5.216956, -2.752936, -5.1787977,
        -12.7987385, -16.287943],
       [124.16676, 28.273184, 37.864815, 14.073718, 17.759731, 2.8795216, -5.557041, -1.9847407, -2.2257912, -6.9401817,
        -8.334572, -12.292275]]
V_Silence = [
    [57.042175, 16.256304, 21.31035, -0.15033218, 11.881158, -1.6687716, 10.720648, 0.018106757, 14.821549, -0.8251362,
     0.61675274, -9.019106],
    [53.656002, 14.188825, 21.311287, -0.56138396, 12.368311, -7.3504043, 10.538454, -2.2609138, 13.715401, -0.9983891,
     6.0700655, -8.139928],
    [57.021843, 3.0813668, 15.133972, -1.79607, 17.281084, -6.4275293, 10.971098, -5.232038, 10.351609, -4.6302047,
     8.062995, -3.8099697],
    [61.405037, 10.843434, 23.90456, -1.1154921, 16.370554, -5.8459177, 14.103179, -4.859748, 7.7005677, -6.809945,
     7.291586, -6.6885242],
    [63.234753, 16.558119, 28.28474, 1.9607797, 12.363835, -7.4432225, 13.879575, -5.858349, 7.574596, -3.8855186,
     5.8540626, -8.4533],
    [53.216908, 11.383955, 20.462309, -1.2970238, 12.09147, -8.057778, 17.806896, -3.6988761, 8.451129, -4.3653555,
     2.5527868, -8.596714],
    [53.891106, 8.231101, 25.7506, 0.930652, 16.538155, -2.0935464, 18.48408, -2.7828178, 10.030334, -1.1063812,
     4.8054013, -11.182437],
    [54.69517, 12.307892, 32.69486, 8.4828005, 17.71221, -3.6655765, 13.322057, -4.6016684, 10.977774, 1.8589101,
     7.625835, -12.70068],
    [63.837975, 18.997143, 27.882772, 6.743929, 13.688854, -7.0393085, 12.358916, -4.5304933, 11.367598, 0.5818075,
     7.269901, -12.26739],
    [73.08328, 23.641665, 23.473082, -0.86669785, 14.428657, -4.2488303, 7.4572506, -2.937108, 13.135923, -3.330823,
     8.187703, -6.13975],
    [73.29113, 17.282984, 21.660906, -3.591044, 11.06938, -3.8546805, 12.691381, -4.1344624, 11.68122, -2.096994,
     9.31814, -4.407849],
    [65.87113, 15.729201, 22.579031, 2.3436937, 11.142277, -3.3420231, 13.439441, -2.3492641, 13.831518, 1.1271998,
     10.558513, -7.604386],
    [58.594437, 16.099825, 24.606407, 2.1443086, 8.821152, -8.216927, 10.01299, -0.22257152, 16.443016, 0.04987825,
     7.487457, -7.4767094],
    [51.055645, 9.697788, 25.910635, 2.4234023, 13.554514, -5.776376, 11.266456, -1.6252795, 11.969547, -1.9418913,
     9.34251, -0.8986918],
    [51.588192, 6.917159, 22.759737, 4.3538756, 18.835358, 5.420483, 15.59319, -5.276758, 8.3522415, -7.797897,
     7.929853, -1.2461413],
    [64.072, 17.521187, 20.55808, -0.70362973, 20.26861, 5.523137, 10.114798, -10.573507, 8.5433855, -12.172383,
     5.8636723, -8.931094],
    [64.2405, 16.8936, 20.71074, 0.18255265, 22.68534, 1.6839005, 2.7893884, -6.6097426, 6.442152, -15.401371,
     3.7926059, -7.1599026]]


def audio2vowel(audio_data: np.ndarray) -> dict[str, float]:
    audio_data = channel_conversion(audio_data)

    # 对线性声谱图应用mel滤波器后，取log，得到log梅尔声谱图，然后对log滤波能量（log梅尔声谱）做DCT离散余弦变换（傅里叶变换的一种），然后保留第2到第13个系数，得到的这12个系数就是MFCC
    n_fft = 512 if audio_data.size >= 512 else audio_data.size
    mfccs = librosa.feature.mfcc(y=audio_data, sr=22050, n_fft=512, dct_type=1, n_mfcc=13)[
            1:].T  # 13个系数 从0开始 取1到13个共12个

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

    # return {
    #     'VoiceSilence': si_r,
    #     'VoiceA': a_r,
    #     'VoiceI': i_r,
    #     'VoiceU': u_r,
    #     'VoiceE': e_r,
    #     'VoiceO': o_r,
    # }

    return {
        'VoiceSilence': si_r if si_r != max else 1,
        'VoiceA': a_r if a_r != max else 0.9,
        'VoiceI': i_r if i_r != max else 0.9,
        'VoiceU': u_r if u_r != max else 0.9,
        'VoiceE': e_r if e_r != max else 0.9,
        'VoiceO': o_r if o_r != max else 0.9,
    }


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

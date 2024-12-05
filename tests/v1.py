import time

import librosa.feature
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import soundfile as sf
from dtw import dtw
from numpy import ndarray

plt.ion()

fig, ax = plt.subplots(nrows=3, sharex=True)  # 创建图


# plt.ylim(-100, 100)  # Y轴取值范围
# plt.yticks([-12 + 2 * i for i in range(13)], [-12 + 2 * i for i in range(13)])  # Y轴刻度
# plt.xlim(0, 100)  # X轴取值范围
# plt.xticks([0.5 * i for i in range(14)], [0.5 * i for i in range(14)])  # X轴刻度
# plt.title("t")  # 标题
# plt.xlabel("X")  # X轴标签
# plt.ylabel("Y")  # Y轴标签
# x, y = [], []  # 用于保存绘图数据，最开始时什么都没有，默认为空
# ax[0].set(title='MFCC')


def audio2db2(audio_data: ndarray) -> float:
    # print(audio_data.ndim)
    # print(audio_data.shape)
    # 如果音频数据为立体声，则将其转换为单声道
    if audio_data.ndim == 2 and audio_data.shape[1] == 2:
        audio_data = audio_data[:, 0]
    # 采样
    # audio_data = audio_data[0:len(audio_data):80]
    # 替换Nan为0
    # audio_data = np.nan_to_num(audio_data)
    # 计算频谱图
    spectrogram = librosa.stft(audio_data)
    # print(spectrogram[0])
    # 将幅度转换为分贝
    spectrogram_db = librosa.amplitude_to_db((np.abs(spectrogram)) ** 2)

    spectrogram_db = spectrogram_db[0:len(audio_data):80]
    # print(spectrogram_db[0])
    # print(spectrogram_db.shape)
    min = np.min(spectrogram_db)
    print(f"min :{min}")
    min = -100
    max = np.max(spectrogram_db)
    print(f"max :{max}")
    # max = 50
    mean = spectrogram_db.mean()
    print(f"mean :{mean}")
    std = spectrogram_db.std()
    print(f"std :{std}")
    y = (mean - min) / (max - min)
    print(y)
    return y


def audio2db(audio_data: bytes) -> float:
    # 将数据转换为 NumPy 数组
    print(len(audio_data))
    audio_data = np.frombuffer(audio_data, dtype=np.float16)
    print(len(audio_data))

    # 如果音频数据为立体声，则将其转换为单声道
    if len(audio_data.shape) > 1 and audio_data.shape[1] == 2:
        audio_data = audio_data[:, 0]

    # 采样
    audio_data = audio_data[0:len(audio_data):80]
    # 替换Nan为0
    audio_data = np.nan_to_num(audio_data)
    # 计算频谱图
    spectrogram = librosa.stft(audio_data)
    # 将幅度转换为分贝
    spectrogram_db = librosa.amplitude_to_db(np.abs(spectrogram))

    print(spectrogram_db.mean())
    print(spectrogram_db.std())

    return spectrogram_db.std()


def audio_test(audio_data: ndarray, axi: int) -> np.array:
    # 如果音频数据为立体声，则将其转换为单声道
    if audio_data.ndim == 2 and audio_data.shape[1] == 2:
        audio_data = audio_data[:, 0]

    # spectrogram = librosa.stft(audio_data, n_fft=audio_data.size)
    # spectrogram_abs = np.abs(spectrogram)
    # https://www.zdaiot.com/DeepLearningApplications/%E8%AF%AD%E9%9F%B3%E5%90%88%E6%88%90/%E8%AF%AD%E9%9F%B3%E5%9F%BA%E7%A1%80%E7%9F%A5%E8%AF%86/
    # 对线性声谱图应用mel滤波器后，取log，得到log梅尔声谱图，然后对log滤波能量（log梅尔声谱）做DCT离散余弦变换（傅里叶变换的一种），然后保留第2到第13个系数，得到的这12个系数就是MFCC
    mfccs = librosa.feature.mfcc(y=audio_data, sr=22050, n_fft=512, dct_type=1, n_mfcc=3)[1:]
    # 13个系数 从0开始 取1到13个共12个
    print(mfccs.ndim)
    print(mfccs.shape)
    print(mfccs)
    print(mfccs.T)
    buf = [[j for j in i] for i in mfccs.T]
    print(buf)
    img = librosa.display.specshow(data=mfccs, ax=ax[axi])
    # fig.colorbar(img, ax=[ax[axi]])
    return mfccs.T


fs1 = np.empty(0, dtype=np.float32)
fs2 = np.empty(0, dtype=np.float32)

with sf.SoundFile('silence2.mp3') as f:
    fs = np.empty(0, dtype=np.float32)

    for i in range(1000000):
        # 8192bits 为一个元音的大致长度 这个长度与采样率有关
        data = f.read(4096, dtype=np.float32)
        if not len(data):
            print(i)
            break
        fs = np.append(fs, data)
        if i == 40:
            fs1 = data

with sf.SoundFile('aiueo.wav') as f:
    fs = np.empty(0, dtype=np.float32)

    for i in range(1000000):
        # 8192bits 为一个元音的大致长度 这个长度与采样率有关
        data = f.read(4096, dtype=np.float32)
        if not len(data):
            print(i)
            break

        fs = np.append(fs, data)
        # A3 I13 U23 E35 O46
        if i == 46:
            fs2 = data

mfcc1 = audio_test(fs1, 1)
mfcc2 = audio_test(fs2, 2)
# audio_test(fs, 0)

dtwv = dtw(mfcc1, mfcc2, distance_only=True)
print(dtwv.distance)
print(dtwv.normalizedDistance)

# vowel1 = analyser.audio2vowel(fs1)
# vowel2 = analyser.audio2vowel(fs2)
# print(vowel1)
# print(vowel2)

with sd.OutputStream(samplerate=f.samplerate,
                     blocksize=8192,
                     channels=1,
                     dtype=np.float32) as stream:
    stream.write(fs1)

time.sleep(5)

with sd.OutputStream(samplerate=f.samplerate,
                     blocksize=8192,
                     channels=2,
                     dtype=np.float32) as stream:
    stream.write(fs2)

plt.pause(100000000000)

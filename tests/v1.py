import audioread
import pyaudio
import librosa
import matplotlib.pyplot as plt
import numpy as np
from numpy import ndarray
import os
import math
import soundfile as sf
from audioread import AudioFile

from typing import Any, BinaryIO, Callable, Generator, Optional, Tuple, Union, List

plt.ion()

fig = plt.figure()  # 创建图
# plt.ylim(-100, 100)  # Y轴取值范围
# plt.yticks([-12 + 2 * i for i in range(13)], [-12 + 2 * i for i in range(13)])  # Y轴刻度
# plt.xlim(0, 100)  # X轴取值范围
# plt.xticks([0.5 * i for i in range(14)], [0.5 * i for i in range(14)])  # X轴刻度
plt.title("t")  # 标题
plt.xlabel("X")  # X轴标签
plt.ylabel("Y")  # Y轴标签
x, y = [], []  # 用于保存绘图数据，最开始时什么都没有，默认为空


# 播放器 播放的过程中将音频数据发送到分析池 分析池被另一个线程调用并分析数据

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


# with sf.SoundFile('zh.wav') as f:
#     print(f.channels, f.samplerate, f.frames)
#     for i in range(1000000):
#         data = f.read(2048, dtype=np.float32)
#         if not len(data):
#             break
#         spectrogram_db = audio2db2(data)
#         x.append(i)
#         y.append(spectrogram_db)
#         plt.plot(x, y)
#         plt.pause(1)

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=2048)

for i in range(10000):
    # while True:
    data = stream.read(2048)
    audio_data = np.frombuffer(data, dtype=np.float32)
    spectrogram_db = audio2db2(audio_data)

    x.append(i)
    y.append(spectrogram_db)
    plt.plot(x, y)
    plt.pause(1)

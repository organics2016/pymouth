import time

import numpy as np
import soundfile as sf

from src.pymouth import VowelAnalyser


def callback(md: dict[str, float], data):
    """
    md like is:
    {
        'VoiceSilence': 0,
        'VoiceA': 0.6547555255,
        'VoiceI': 0.2872873444,
        'VoiceU': 0.1034789232,
        'VoiceE': 0.3927834533,
        'VoiceO': 0.1927834548,
    }
    """
    print(md)


def get_block(index: int) -> np.ndarray:
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
            if i == index:
                return data


with VowelAnalyser() as a:
    a.action_noblock(get_block(3), 44100, output_device=3, callback=callback, block_size=4096)
    a.action_noblock(get_block(13), 44100, output_device=3, callback=callback, block_size=4096)
    a.action_noblock(get_block(23), 44100, output_device=3, callback=callback, block_size=4096)
    a.action_noblock(get_block(34), 44100, output_device=3, callback=callback, block_size=4096)
    a.action_noblock(get_block(46), 44100, output_device=3, callback=callback, block_size=4096)
    print("end")
    time.sleep(1000000)

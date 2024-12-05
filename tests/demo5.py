import time

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


with VowelAnalyser() as a:
    a.action_noblock('zh.wav', 44100, output_device=2, callback=callback)
    # a.sync_action()
    print("end")
    time.sleep(1000000)

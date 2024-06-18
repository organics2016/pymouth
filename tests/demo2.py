import time

from src.pymouth import DBAnalyser


def callback(y, data):
    print(y)

with DBAnalyser('zh.wav', 44100, output_channels=1, callback=callback) as a:
    a.async_action()
    # a.sync_action()
    print("end")
    time.sleep(1000000)
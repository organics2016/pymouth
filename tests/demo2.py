import time

from src.pymouth import DBAnalyser


def callback(y: float, data):
    print(y)


with DBAnalyser() as a:
    a.async_action('zh.wav', 44100, output_device=2, callback=callback)
    # a.sync_action()
    print("end")
    time.sleep(1000000)

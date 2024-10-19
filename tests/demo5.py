import threading
from time import sleep

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import DBAnalyser


def t1():
    with VTSAdapter(DBAnalyser) as a:
        a.action_block(audio='light_the_sea.wav', samplerate=44100, output_device=2)
        print("end")


def main():
    threading.Thread(target=t1).start()
    sleep(10000)
    print("end main")


if __name__ == "__main__":
    main()

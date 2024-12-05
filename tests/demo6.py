import time

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import VowelAnalyser


def main():
    with VTSAdapter(VowelAnalyser) as a:
        a.sync_action(audio='aiueo.wav', samplerate=44100, output_device=2)
        print('end')
        time.sleep(100000)


if __name__ == "__main__":
    main()

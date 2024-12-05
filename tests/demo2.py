import time

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import VowelAnalyser


def main():
    with VTSAdapter(VowelAnalyser) as a:
        a.action(audio='light_the_sea.wav', samplerate=44100, output_device=2)
        time.sleep(100000)  # do something


if __name__ == "__main__":
    main()

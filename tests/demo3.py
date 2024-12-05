import asyncio

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import VowelAnalyser


async def main():
    with VTSAdapter(VowelAnalyser) as a:
        a.action(audio='aiueo.wav', samplerate=44100, output_device=2)
        # a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2)
        await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())

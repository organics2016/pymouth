import asyncio

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import VowelAnalyser


async def main():
    async with VTSAdapter(VowelAnalyser) as a:
        await a.action(audio='light_the_sea.wav', samplerate=44100, output_device=2)
        await asyncio.sleep(2)
        await a.action(audio='light_the_sea.wav', samplerate=44100, output_device=2)
        await asyncio.sleep(1000000000)


if __name__ == "__main__":
    asyncio.run(main())

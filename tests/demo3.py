import asyncio

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import VowelAnalyser


async def main():
    async with VTSAdapter(VowelAnalyser) as a:
        await a.action(audio='aiueo.mp3', samplerate=44100, output_device=2)
        await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())

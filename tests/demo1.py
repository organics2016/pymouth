import asyncio

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import DBAnalyser


def finished_callback():
    print("finished_callback")


async def main():
    async with VTSAdapter(DBAnalyser) as a:
        await a.action(audio='light_the_sea.wav',
                       samplerate=44100,
                       output_channels=2,
                       finished_callback=finished_callback)

        await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())

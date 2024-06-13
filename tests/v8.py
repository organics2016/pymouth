import asyncio

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import DBAnalyser


def finished_callback():
    print("finished_callback")


async def main():
    async with VTSAdapter(DBAnalyser) as a:
        await a.action(audio='zh.wav', samplerate=44100, output_channels=1)
        await asyncio.sleep(100000)

    # async with VTSAdapter(DBAnalyser) as a:
    #     await a.action('zh.wav', 44100, output_channels=1, finished_callback=finished_callback)
    #     await asyncio.sleep(40)
    #     await a.action('zh.wav', 44100, output_channels=1, finished_callback=finished_callback)
    #     await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())

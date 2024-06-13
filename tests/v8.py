import asyncio

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import DBAnalyser


async def main():


    async with VTSAdapter(DBAnalyser) as a:
        await a.action('zh.wav', 44100, output_channels=1)
        await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())

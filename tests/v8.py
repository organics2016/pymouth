import asyncio
from src.pymouth.adapter import VTSAdapter


async def main():
    async with VTSAdapter() as a:
        print("11111")
        await a.action('zh.wav', 44100, channels=1)
        print("22222")
        await asyncio.sleep(100000)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import threading
import time
import traceback
from concurrent.futures.thread import ThreadPoolExecutor

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import DBAnalyser


def thread_pool_callback(worker):
    print(f"thread_pool_callback ...{threading.current_thread().name}")
    worker_exception = worker.exception()
    if worker_exception:
        print(f"ex: {worker_exception}")
        traceback.print_exc()


async def t1():
    print(threading.current_thread().name)
    async with VTSAdapter(DBAnalyser) as a:
        # await asyncio.sleep(300)
        await a.action(audio='light_the_sea.wav', samplerate=44100, output_device=2)
        # await asyncio.sleep(2)
        # await a.action(audio='light_the_sea.wav', samplerate=44100, output_device=2)
        print("end")
        await asyncio.sleep(100000)


def main():
    with ThreadPoolExecutor(2) as executor:
        executor.submit(asyncio.run, t1())

    print("end main")
    time.sleep(100000)


if __name__ == "__main__":
    main()

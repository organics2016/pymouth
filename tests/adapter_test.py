import asyncio
import time
import unittest

from src.pymouth.adapter import VTSAdapter
from src.pymouth.analyser import VowelAnalyser, DBAnalyser


class AdapterAsyncTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.finish = 0

    async def test_async_block_db(self):
        with VTSAdapter(DBAnalyser()) as a:
            a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2)
            a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2)
            print('test_async_block_db end')

    def test_noblock_db_callback(self):
        self.finish += 1

    async def test_async_noblock_db(self):
        with VTSAdapter(DBAnalyser()) as a:
            a.action(audio='aiueo.wav', samplerate=44100, output_device=2,
                     finished_callback=self.test_noblock_db_callback)
            a.action(audio='aiueo.wav', samplerate=44100, output_device=2,
                     finished_callback=self.test_noblock_db_callback)
            while self.finish < 2:
                await asyncio.sleep(1)
                continue
            print('test_async_noblock_db end')


class AdapterTest(unittest.TestCase):

    def setUp(self):
        self.finish = 0

    def test_block_db(self):
        with VTSAdapter(VowelAnalyser()) as a:
            a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2)
            a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2)
            print('test_block_db end')

    # @unittest.skip
    def test_noblock_db_callback(self):
        self.finish += 1

    def test_noblock_db(self):
        with VTSAdapter(VowelAnalyser()) as a:
            a.action(audio='aiueo.wav', samplerate=44100, output_device=2,
                     finished_callback=self.test_noblock_db_callback)
            a.action(audio='aiueo.wav', samplerate=44100, output_device=2,
                     finished_callback=self.test_noblock_db_callback)
            while self.finish < 2:
                time.sleep(1)
                continue
            print('test_noblock_db end')

import numpy as np
import soundfile as sf
import pyvts
import asyncio
from typing import Type
from .analyser import Analyser, DBAnalyser


class VTSAdapter:
    def __init__(self,
                 analyser: Type[Analyser],
                 db_mouth_bind_param: str = 'MouthOpen',
                 plugin_info: dict = None,
                 vts_api: dict = None
                 ):

        if plugin_info is None:
            plugin_info = {"plugin_name": "pymouth",
                           "developer": "organics",
                           "authentication_token_path": "./pymouth_vts_token.txt",
                           "plugin_icon": None}

        if vts_api is None:
            vts_api = {
                "version": "1.0",
                "name": "VTubeStudioPublicAPI",
                "port": 8001
            }

        self.analyser = analyser
        self.db_mouth_bind_param = db_mouth_bind_param
        self.plugin_info = plugin_info
        self.vts_api = vts_api

        self.vts = pyvts.vts(plugin_info=self.plugin_info, vts_api_info=self.vts_api)
        self.event_loop = asyncio.get_event_loop()

    async def __aenter__(self):
        await self.vts.connect()
        try:
            await self.vts.read_token()
            auth = await self.vts.request_authenticate()  # use token
            if not auth:
                raise Exception('Not fond token or the token is expired')

        except Exception as e:
            print(e)
            await self.vts.request_authenticate_token()  # get token
            await self.vts.write_token()
            auth = await self.vts.request_authenticate()  # use token
            if not auth:
                raise Exception('VTubeStudio Server error')

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.vts.close()

    def __db_callback(self, y, data):

        async def dd():
            await self.vts.request(
                self.vts.vts_request.requestSetParameterValue(
                    parameter=self.db_mouth_bind_param,
                    value=y,
                )
            )

        asyncio.run_coroutine_threadsafe(dd(), self.event_loop)

    async def action(self,
                     audio: np.ndarray | str | sf.SoundFile,
                     samplerate: int | float,
                     output_channels: int,
                     auto_play: bool = True):

        if self.analyser == DBAnalyser:
            with DBAnalyser(audio=audio,
                            samplerate=samplerate,
                            output_channels=output_channels,
                            callback=self.__db_callback,
                            auto_play=auto_play) as a:
                a.async_action()

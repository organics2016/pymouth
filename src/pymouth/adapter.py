import numpy as np
import soundfile as sf
import pyvts
import asyncio
from .analyser import AudioAnalyser


class VTSAdapter:
    def __init__(self,
                 plugin_info: dict = None,
                 vts_api: dict = None,
                 mouth_bind_param: str = 'MouthOpen'):

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

        self.plugin_info = plugin_info
        self.vts_api = vts_api
        self.vts = pyvts.vts(plugin_info=self.plugin_info, vts_api_info=self.vts_api)
        self.mouth_bind_param = mouth_bind_param
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

    def __callback(self, y, data):

        async def dd():
            return await self.vts.request(
                self.vts.vts_request.requestSetParameterValue(
                    parameter=self.mouth_bind_param,
                    value=y,
                )
            )

        asyncio.run_coroutine_threadsafe(dd(), self.event_loop)

    async def action(self,
                     audio: np.ndarray | str | sf.SoundFile,
                     samplerate: int | float,
                     channels: int,
                     auto_play: bool = True):

        with AudioAnalyser(audio=audio,
                           samplerate=samplerate,
                           channels=channels,
                           callback=self.__callback,
                           auto_play=auto_play) as a:
            a.async_action()
            print("end")

import asyncio
from typing import Type

import numpy as np
import pyvts
import soundfile as sf

from .analyser import Analyser, DBAnalyser


class VTSAdapter:
    def __init__(self,
                 analyser: Type[Analyser],
                 db_vts_mouth_param: str = 'MouthOpen',
                 plugin_info: dict = None,
                 vts_api: dict = None
                 ):
        """
        VTubeStudio Adapter.
        :param analyser: 分析仪,必须是 Analyser 的子类
        :param db_vts_mouth_param: 针对于DBAnalyser, VTS中控制mouth的参数,这个参数一般是 'MouthOpen'
        :param plugin_info: 插件信息,可以自定义
        :param vts_api: VTS API的一些配置, 可以自定义 VTS server port
        """

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
        self.db_vts_mouth_param = db_vts_mouth_param
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
                    parameter=self.db_vts_mouth_param,
                    value=y,
                )
            )

        asyncio.run_coroutine_threadsafe(dd(), self.event_loop)

    async def action(self,
                     audio: np.ndarray | str | sf.SoundFile,
                     samplerate: int | float,
                     output_channels: int,
                     auto_play: bool = True):

        """
        将集合均分，每份n个元素
        :param audio: 音频数据, 它可以是文件,也可以是ndarray
        :param samplerate: 采样率, 这取决与音频数据的采样率, 如果你无法获取到音频数据的采样率, 可以尝试输出设备的采样率.
        :param output_channels: 输出设备通道, 这取决与你的硬件, 你也可以使用虚拟设备.
        :param auto_play: 是否自动播放音频, 默认为True, 如果为True,会播放音频(自动将audio写入指定output_channels)
        """

        if self.analyser == DBAnalyser:
            with DBAnalyser(audio=audio,
                            samplerate=samplerate,
                            output_channels=output_channels,
                            callback=self.__db_callback,
                            auto_play=auto_play) as a:
                a.async_action()

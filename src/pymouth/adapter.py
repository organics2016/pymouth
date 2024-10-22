import asyncio
from typing import Type

import numpy as np
import pyvts
import soundfile as sf

from .analyser import Analyser, DBAnalyser, VowelAnalyser


class VTSAdapter:
    def __init__(self,
                 analyser: Type[Analyser],
                 db_vts_mouth_param: str = 'MouthOpen',
                 vowel_vts_mouth_param: dict[str, str] = None,
                 plugin_info: dict = None,
                 vts_api: dict = None
                 ):
        """
        VTubeStudio Adapter.
        :param analyser: 分析仪,必须是 Analyser 的子类
        :param db_vts_mouth_param: 仅作用于`DBAnalyser`, VTS中控制mouth_input的参数, 如果不是默认值请自行修改.
        :param vowel_vts_mouth_param: 仅作用于VowelAnalyser, VTS中控制mouth的参数,这个参数默认是 ('VoiceSilence', 'VoiceA', 'VoiceI', 'VoiceU', 'VoiceE', 'VoiceO')
            如果你的VTS中不是这些默认值，你可以通过这个参数修改以匹配你VTS中关于AIUEO的输入参数
            例如：{
                    'VoiceSilence': 'CustomSilence',
                    'VoiceA': 'CustomA',
                    'VoiceI': 'CustomI',
                    'VoiceU': 'CustomU',
                    'VoiceE': 'CustomE',
                    'VoiceO': 'CustomO'
                }
            这个dict中 key 不能变，value 则设置你自己VTS中关于AIUEO的输入参数

        :param plugin_info: 插件信息,可以自定义
        :param vts_api: VTS API的一些配置,这里可以自定义 VTS server port(8001)
        """

        if vowel_vts_mouth_param is None:
            vowel_vts_mouth_param = {
                'VoiceSilence': 'VoiceSilence',
                'VoiceA': 'VoiceA',
                'VoiceI': 'VoiceI',
                'VoiceU': 'VoiceU',
                'VoiceE': 'VoiceE',
                'VoiceO': 'VoiceO'
            }

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

        self.analyser = analyser()
        self.db_vts_mouth_param = db_vts_mouth_param
        self.vowel_vts_mouth_param = vowel_vts_mouth_param
        self.plugin_info = plugin_info
        self.vts_api = vts_api

        self.vts = pyvts.vts(plugin_info=self.plugin_info, vts_api_info=self.vts_api)
        # 必须使用 get_running_loop 拿不到会报错，而不是新建 event_loop，event_loop由调用者维护。
        self.event_loop = asyncio.get_running_loop()

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

    # 同步创建方式会导致 websockets 自动断开，使用新线程维护链接任然会断开，此问题暂时无解，这个初始化方法被抛弃
    # def __enter__(self):
    #     # 同步代码需要创建新的 event_loop,因为完全同步调用无协程，所以可以多次调用 run_until_complete, 直到 VTSAdapter 对象生命周期结束
    #     self.event_loop = asyncio.new_event_loop()
    #     self.is_sync = True
    #     self.event_loop.run_until_complete(self.__aenter__())
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.event_loop.run_until_complete(self.__aexit__(exc_type, exc_val, exc_tb))
    #     self.event_loop.close()

    def __db_callback(self, y: float, data):
        async def dd():
            await self.vts.request(
                self.vts.vts_request.requestSetParameterValue(
                    parameter=self.db_vts_mouth_param,
                    value=y,
                )
            )

        # 当前函数由插件自己的线程池调用，event_loop由用户维护，所以需要将插件自己的线程绑定到主event_loop
        asyncio.run_coroutine_threadsafe(dd(), self.event_loop)

    def __vowel_callback(self, vowel_dict: dict, data):
        async def dd():
            keys = [self.vowel_vts_mouth_param[x] for x in vowel_dict.keys()]
            values = [x for x in vowel_dict.values()]
            await self.vts.request(
                self.vts.vts_request.requestSetMultiParameterValue(
                    parameters=keys,
                    values=values
                )
            )

        asyncio.run_coroutine_threadsafe(dd(), self.event_loop)

    async def action(self,
                     audio: np.ndarray | str | sf.SoundFile,
                     samplerate: int | float,
                     output_device: int,
                     finished_callback=None,
                     auto_play: bool = True):

        """
        启动分析器开始分析音频数据, 注意:此方法为非阻塞方法,会立即返回
        :param audio: 音频数据, 可以是文件path, 可以是SoundFile对象, 也可以是ndarray
        :param samplerate: 采样率, 这取决与音频数据的采样率, 如果你无法获取到音频数据的采样率, 可以尝试输出设备的采样率.
        :param output_device: 输出设备Index, 这取决与硬件或虚拟设备. 可用 audio_devices_utils.py 打印当前系统音频设备信息
        :param finished_callback: 音频处理完成后,会回调这个方法
        :param auto_play: 是否自动播放音频,默认为True,会播放音频(自动将audio写入指定`output_device`)
        """

        if isinstance(self.analyser, DBAnalyser):
            self.analyser.async_action(audio,
                                       samplerate,
                                       output_device,
                                       self.__db_callback,
                                       finished_callback,
                                       auto_play,
                                       block_size=2048)
        elif isinstance(self.analyser, VowelAnalyser):
            self.analyser.async_action(audio,
                                       samplerate,
                                       output_device,
                                       self.__vowel_callback,
                                       finished_callback,
                                       auto_play,
                                       block_size=4096)

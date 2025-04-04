import numpy as np
import soundfile as sf

from .analyser import Analyser, DBAnalyser, VowelAnalyser
from .vts_websockets import VTSWebSocket, VTSPluginInfo, VTSParameterData


class VTSAdapter:
    def __init__(self,
                 analyser: Analyser,
                 db_vts_mouth_param: str = 'MouthOpen',
                 vowel_vts_mouth_param: dict[str, str] = None,
                 ws_uri: str = 'ws://localhost:8001',
                 plugin_info: VTSPluginInfo = VTSPluginInfo(plugin_name='pymouth',
                                                            developer='organics',
                                                            authentication_token_path='./pymouth_vts_token.txt',
                                                            plugin_icon=None)
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

        :param ws_uri: websocket uri 默认：ws://localhost:8001
        :param plugin_info: 插件信息,可以自定义
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

        self.analyser = analyser

        self.db_vts_mouth_param = db_vts_mouth_param
        self.vowel_vts_mouth_param = vowel_vts_mouth_param

        self.ws_uri = ws_uri
        self.plugin_info = plugin_info
        self.vts = VTSWebSocket(ws_uri, plugin_info)

    def __enter__(self):
        self.vts.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.vts.close()

    def __db_callback(self, y: float, data):
        self.vts.set_single_param(VTSParameterData(self.db_vts_mouth_param, y))

    def __vowel_callback(self, vowel_dict: dict, data):
        params = [VTSParameterData(self.vowel_vts_mouth_param[k], v) for k, v in vowel_dict.items()]
        self.vts.set_params(params)

    def action(self,
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
            self.analyser.action_noblock(audio,
                                         samplerate,
                                         output_device,
                                         self.__db_callback,
                                         finished_callback,
                                         auto_play,
                                         block_size=4096)
        elif isinstance(self.analyser, VowelAnalyser):
            self.analyser.action_noblock(audio,
                                         samplerate,
                                         output_device,
                                         self.__vowel_callback,
                                         finished_callback,
                                         auto_play,
                                         block_size=4096)

    def action_block(self,
                     audio: np.ndarray | str | sf.SoundFile,
                     samplerate: int | float,
                     output_device: int,
                     finished_callback=None,
                     auto_play: bool = True):

        if isinstance(self.analyser, DBAnalyser):
            self.analyser.action_block(audio,
                                       samplerate,
                                       output_device,
                                       self.__db_callback,
                                       finished_callback,
                                       auto_play,
                                       block_size=4096)
        elif isinstance(self.analyser, VowelAnalyser):
            self.analyser.action_block(audio,
                                       samplerate,
                                       output_device,
                                       self.__vowel_callback,
                                       finished_callback,
                                       auto_play,
                                       block_size=4096)

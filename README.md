[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pymouth)]()
[![PyPI - License](https://img.shields.io/pypi/l/pymouth)](https://github.com/organics2016/pymouth/blob/master/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/pymouth?color=green)](https://pypi.org/project/pymouth/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pymouth)](https://pypi.org/project/pymouth/)

# pymouth

`pymouth` 是基于Python的Live2D口型同步库. 你可以用音频文件, 甚至是AI模型输出的ndarray, 就能轻松的让你的Live2D形象开口
唱跳RAP ~v~.<br>
效果演示视频.
[Demo video](https://www.bilibili.com/video/BV1nKGoeJEQY/?vd_source=49279a5158cf4b9566102c7e3806c231)

## Quick Start

### Environment

- Python>=3.10
- VTubeStudio>=1.28.0 (可选)

### Installation

```shell
pip install pymouth
```

### Get Started

1. 在开始前你需要打开 `VTubeStudio` 的 Server 开关. 端口一般默认是8001.<br>
   ![server_start.png](https://github.com/organics2016/pymouth/blob/master/screenshot/server_start.png)
2. 你需要确定自己Live2D口型同步的支持参数.<br>
   请注意：下面提供一种简单的判断方式，但这种方式会修改(重置)Live2D模型口型部分参数，使用前请备份好自己的模型。<br>
   如果你对自己的模型了如指掌，可以跳过这步。<br>
   ![setup.png](https://github.com/organics2016/pymouth/blob/master/screenshot/setup.png)
    - 确认重置参数后，如果出现以下信息，则说明你的模型仅支持 `基于分贝的口型同步`
      ![db.png](https://github.com/organics2016/pymouth/blob/master/screenshot/db.png)
    - 确认重置参数后，如果出现以下信息，则说明你的模型仅支持 `基于元音的口型同步`
      ![vowel.png](https://github.com/organics2016/pymouth/blob/master/screenshot/vowel.png)
    - 如果VTubeStudio找到了所有参数，并且重置成功，说明两种方式都支持。只需要在接下来的代码中选择一种方式即可.

3. 下面是两种基于不同方式的Demo.<br>
   你可以找一个音频文件替换`some.wav`.<br>
   `samplerate`:音频数据的采样率.<br>
   `output_device`:输出设备Index.
   可以参考[audio_devices_utils.py](https://github.com/organics2016/pymouth/blob/master/src/pymouth/audio_devices_utils.py)<br>
    - `基于分贝的口型同步`
       ```python
       import time
       from pymouth import VTSAdapter, DBAnalyser
    
       def main():
         with VTSAdapter(DBAnalyser) as a:
             a.action(audio='some.wav', samplerate=44100, output_device=2)
             time.sleep(100000)  # do something
    
    
       if __name__ == "__main__":
         main()
       ```

    - `基于元音的口型同步`
       ```python
       import time
       from pymouth import VTSAdapter, VowelAnalyser
    
       def main():
         with VTSAdapter(VowelAnalyser) as a:
             a.action(audio='some.wav', samplerate=44100, output_device=2)
             time.sleep(100000)  # do something
    
    
       if __name__ == "__main__":
         main()
       ```

      第一次运行程序时, `VTubeStudio`会弹出插件授权界面, 通过授权后, 插件会在runtime路径下生成`pymouth_vts_token.txt`文件,
      之后运行不会重复授权, 除非token文件丢失或在`VTubeStudio`移除授权.<br>

## API变化

1.2.0版本之后，移除了所有函数的协程调用方式(async/await)，协程调用具有传染性，不利于用户维护。<br>
目前只提供阻塞与非阻塞调用方式，非阻塞方式由内部线程池单线程实现，即无论`a.action`
被调用多少次，都会按照调用的现后顺序播放音频。<br>

- 如果你仍使用协程启动，可以参考下面的示例
   ```python
   import asyncio
   from pymouth import VTSAdapter, VowelAnalyser
   
   
   async def main():
       with VTSAdapter(VowelAnalyser) as a:
           a.action(audio='aiueo.wav', samplerate=44100, output_device=2)  # no-block
           # a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2) # block
           await asyncio.sleep(100000)
   
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

## About AI(废弃，下面的例子任然使用旧版本的协程调用方式，1.2.0以后的版本需要稍作修改)

下面是一个比较完整的使用pymouth作为AI TTS消费者的例子。

```python
import asyncio.queues as queues
import logging
import time
import asyncio
from asyncio import QueueFull
from melo.api import TTS
from pymouth import VTSAdapter, DBAnalyser
from concurrent.futures.thread import ThreadPoolExecutor


class SpeakMsg:
    def __init__(self, msg: str, required: bool):
        self.msg = msg
        self.required = required
        self.create_timestamp = time.time()
        self.create_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.create_timestamp))


class Speaker:
    def __init__(self):
        self.queue = queues.Queue(2)
        self.ready = True

    def finished_callback(self):
        self.ready = True

    async def start(self):
        tts_model = TTS(language='ZH', device='cuda:0')
        speaker_ids = tts_model.hps.data.spk2id

        plugin_info = {"plugin_name": "kanojyo2",
                       "developer": "organics",
                       "authentication_token_path": "./pymouth_vts_token.txt",
                       "plugin_icon": None}

        async with VTSAdapter(DBAnalyser, plugin_info=plugin_info) as a:
            while True:
                msg: SpeakMsg = await self.queue.get()
                audio = tts_model.tts_to_file(msg.msg, speaker_ids['ZH'], output_path=None, speed=1.0)

                # a.action() 会立即返回，但音频可能还在播放，再未播放完音频前重新消费可能不是你所期望的。
                # 尽管 pymouth 会自己管理音频播放顺序(自己管理播放队列，同一时刻只会播放一段音频)。但像下面这样阻断消费可能是更好的选择
                while not self.ready:
                    await asyncio.sleep(1)
                self.ready = False

                await a.action(audio=audio,
                               samplerate=tts_model.hps.data.sampling_rate,
                               output_device=2,
                               finished_callback=self.finished_callback)

    async def speak(self, msg: str, required=True):
        if required:
            await self.queue.put(SpeakMsg(msg, required))
        else:
            try:
                self.queue.put_nowait(SpeakMsg(msg, required))
            except QueueFull:
                logging.warning('Queue is full')


speakers = Speaker()
event_loop = asyncio.get_event_loop()


def producer_callback(msg: str):
    async def mm():
        await speakers.speak(msg)

    # 生产者可能来自于不同线程，需要event_loop跨线程调用
    asyncio.run_coroutine_threadsafe(mm(), event_loop)


def main():
    with ThreadPoolExecutor(2) as executor:
        # 这里的实现只作为参考而不是建议。没有让协程覆盖程序的整个生命周期是因为：对于AI等CPU密集型场景，使用线程而不是协程可能会更好。
        executor.submit(event_loop.run_until_complete, speakers.start())
        # do something


if __name__ == "__main__":
    main()
```

## More Details

### High Level

关键的代码只有两行:

```python
with VTSAdapter(DBAnalyser) as a:
    a.action(audio='some.wav', samplerate=44100, output_device=2)  # no-block
    # a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2) # block
```

`a.action()`非阻塞，会立即返回，由程序内部维护线程池和队列。<br>
`a.action_block()`阻塞，直到音频播放和处理完毕才会返回，纯同步代码无线程，线程由调用者维护。<br>

`VTSAdapter`以下是详细的参数说明:

| param                   | required | default         | describe                                                 |
|:------------------------|:---------|:----------------|:---------------------------------------------------------|
| `analyser`              | Y        |                 | 分析仪,必须是 Analyser 的子类,目前支持`DBAnalyser`和`VowelAnalyser`    |
| `db_vts_mouth_param`    |          | `'MouthOpen'`   | 仅作用于`DBAnalyser`, VTS中控制mouth_input的参数, 如果不是默认值请自行修改.    |
| `vowel_vts_mouth_param` |          | `dict[str,str]` | 仅作用于`VowelAnalyser`, VTS中控制mouth_input的参数, 如果不是默认值请自行修改. |
| `ws_uri`                |          | `str`           | websocket uri 默认：ws://localhost:8001                     |
| `plugin_info`           |          | `VTSPluginInfo` | 插件信息,可以自定义                                               |

`a.action()` 会开始处理音频数据. 以下是详细的参数说明:

| param               | required | default | describe                                                        |
|:--------------------|:---------|:--------|:----------------------------------------------------------------|
| `audio`             | Y        |         | 音频数据, 可以是文件path, 可以是SoundFile对象, 也可以是ndarray                    |
| `samplerate`        | Y        |         | 采样率, 这取决与音频数据的采样率, 如果你无法获取到音频数据的采样率, 可以尝试输出设备的采样率.              |
| `output_device`     | Y        |         | 输出设备Index, 这取决与硬件或虚拟设备. 可用 audio_devices_utils.py 打印当前系统音频设备信息. |
| `finished_callback` |          | `None`  | 音频处理完成会回调这个方法.                                                  |
| `auto_play`         |          | `True`  | 是否自动播放音频,默认为True,会播放音频(自动将audio写入指定`output_device`)             |

### Low Level

Get Started 演示了一种High Level API 如果你不使用 `VTubeStudio` 或者想更加灵活的使用, 可以尝试Low Level API. 下面是一个Demo.

```python
import time

from pymouth import DBAnalyser


def callback(y: float, data):
    # Y is the Y coordinate of the model's mouth.
    # Like is 0.4212883452
    print(y)  # do something


with DBAnalyser() as a:
    a.action_noblock('zh.wav', 44100, output_device=2, callback=callback)  # no block
    # a.action_block()  # block
    print("end")
    time.sleep(1000000)
```

```python
import time

from pymouth import VowelAnalyser


def callback(md: dict[str, float], data):
    """
    md like is:
    {
        'VoiceSilence': 0,
        'VoiceA': 0.6547555255,
        'VoiceI': 0.2872873444,
        'VoiceU': 0.1034789232,
        'VoiceE': 0.3927834533,
        'VoiceO': 0.1927834548,
    }
    """
    print(md)  # do something


with VowelAnalyser() as a:
    a.action_noblock('zh.wav', 44100, output_device=2, callback=callback)  # no block
    # a.action_block() # block
    print("end")
    time.sleep(1000000)
```

## TODO

- 文档补全
- Test case

## Special Thanks

- 参考文档:
- [![](https://avatars.githubusercontent.com/u/1933673?s=40)卜卜口](https://github.com/itorr)
  https://github.com/itorr/itorr/issues/7
- https://www.zdaiot.com/DeepLearningApplications/%E8%AF%AD%E9%9F%B3%E5%90%88%E6%88%90/%E8%AF%AD%E9%9F%B3%E5%9F%BA%E7%A1%80%E7%9F%A5%E8%AF%86/
- https://huailiang.github.io/blog/2020/mouth/
- https://zh.wikipedia.org/wiki/%E5%85%B1%E6%8C%AF%E5%B3%B0

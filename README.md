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
    import asyncio
    from pymouth import VTSAdapter, DBAnalyser
    
    
    async def main():
        async with VTSAdapter(DBAnalyser) as a:
            await a.action(audio='some.wav', samplerate=44100, output_device=4)
            await asyncio.sleep(100000)  # do something
    
    
    if __name__ == "__main__":
        asyncio.run(main())
    ```

    - `基于元音的口型同步`
    ```python
    import asyncio
    from pymouth import VTSAdapter, VowelAnalyser
    
    
    async def main():
        async with VTSAdapter(VowelAnalyser) as a:
            await a.action(audio='some.wav', samplerate=44100, output_device=4)
            await asyncio.sleep(100000)  # do something
    
    
    if __name__ == "__main__":
        asyncio.run(main())
    ```

   第一次运行程序时, `VTubeStudio`会弹出插件授权界面, 通过授权后, 插件会在runtime路径下生成`pymouth_vts_token.txt`文件,
   之后运行不会重复授权, 除非token文件丢失或在`VTubeStudio`移除授权.<br>

## More Details

### High Level

关键的代码只有两行,且都是异步的:

```python
async with VTSAdapter(DBAnalyser) as a:
    await a.action(audio='some.wav', samplerate=44100, output_device=4)
```

`VTSAdapter`以下是详细的参数说明:

| param                   | required | default         | describe                                                 |
|:------------------------|:---------|:----------------|:---------------------------------------------------------|
| `analyser`              | Y        |                 | 分析仪,必须是 Analyser 的子类,目前支持`DBAnalyser`和`VowelAnalyser`    |
| `db_vts_mouth_param`    |          | `'MouthOpen'`   | 仅作用于`DBAnalyser`, VTS中控制mouth_input的参数, 如果不是默认值请自行修改.    |
| `vowel_vts_mouth_param` |          | `dict[str,str]` | 仅作用于`VowelAnalyser`, VTS中控制mouth_input的参数, 如果不是默认值请自行修改. |
| `plugin_info`           |          | `dict`          | 插件信息,可以自定义                                               |
| `vts_api`               |          | `dict`          | VTS API的一些配置,这里可以自定义 VTS server port(8001)               |

`await a.action()` 会开始处理音频数据. 以下是详细的参数说明:

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


def callback(y, data):
    print(y)  # do something


with DBAnalyser('zh.wav', 44100, output_device=4, callback=callback) as a:
    a.async_action()  # no block
    # a.sync_action() # block
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

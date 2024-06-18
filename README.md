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

注意: 在开始前你需要打开 `VTubeStudio` 的 Server 开关. 端口一般默认是8001.<br>
下面是一个完整的Demo,你可以找一个音频文件替换`some.wav`.<br>

```python
import asyncio
from pymouth import VTSAdapter, DBAnalyser


async def main():
    async with VTSAdapter(DBAnalyser) as a:
        await a.action(audio='some.wav', samplerate=44100, output_channels=1)
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
    await a.action(audio='some.wav', samplerate=44100, output_channels=1)
```

`async with VTSAdapter(DBAnalyser) as a:` 用来描述需要用到的 `Adapter` 和 `Analyser`.
目前支持的 `Adapter` 只有 `VTSAdapter`, 支持的 `Analyser` 只有 `DBAnalyser`. 如果真有人用的话可能会适配更多.
以下是详细的参数说明:

| param                | required | default       | describe                                                              |
|:---------------------|:---------|:--------------|:----------------------------------------------------------------------|
| `analyser`           | Y        |               | 分析仪,必须是 Analyser 的子类,目前只支持`DBAnalyser`                                |
| `db_vts_mouth_param` |          | `'MouthOpen'` | 针对于`DBAnalyser`, VTS中控制mouth_input的参数,这个参数一般是 'MouthOpen', 如果不是请自行修改. |
| `plugin_info`        |          | `None`        | 插件信息,一般不用改,可以自定义.                                                     |
| `vts_api`            |          | `None`        | VTS API的一些配置,一般不用改, 这里可以自定义 VTS server port(8001)                     |

`await a.action(audio='some.wav', samplerate=44100, output_channels=1)` 会开始处理音频数据. 以下是详细的参数说明:

| param               | required | default | describe                                                      |
|:--------------------|:---------|:--------|:--------------------------------------------------------------|
| `audio`             | Y        |         | 音频数据, 可以是文件path, 可以是SoundFile对象, 也可以是ndarray                  |
| `samplerate`        | Y        |         | 采样率, 这取决与音频数据的采样率, 如果你无法获取到音频数据的采样率, 可以尝试输出设备的采样率.            |
| `output_channels`   | Y        |         | 输出设备通道, 这取决与你的硬件, 你也可以使用虚拟设备.                                 |
| `finished_callback` |          | `None`  | 音频处理完成会回调这个方法                                                 |
| `auto_play`         |          | `True`  | 是否自动播放音频, 默认为True, 如果为True,会播放音频(自动将audio写入指定output_channels) |

### Low Level

Get Started 演示了一种High Level API 如果你不使用 `VTubeStudio` 或者想更加灵活的使用, 可以尝试Low Level API. 下面是一个Demo.

```python
import time
from pymouth import DBAnalyser


def callback(y, data):
    print(y)  # do something


with DBAnalyser('zh.wav', 44100, output_channels=1, callback=callback) as a:
    a.async_action()  # no block
    # a.sync_action() # block
    print("end")
    time.sleep(1000000)
```

## TODO

- 文档补全
- CI
- 基于元音的口型同步API
- Test case

## Special Thanks

Idea源:
[![](https://avatars.githubusercontent.com/u/1933673?s=40)卜卜口](https://github.com/itorr)

https://github.com/itorr/itorr/issues/7
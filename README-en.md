[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pymouth)]()
[![PyPI - License](https://img.shields.io/pypi/l/pymouth)](https://github.com/organics2016/pymouth/blob/master/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/pymouth?color=green)](https://pypi.org/project/pymouth/)
[![PyPI Downloads](https://static.pepy.tech/badge/pymouth)](https://pepy.tech/projects/pymouth)

# pymouth

`pymouth` is a Python-based Live2D lip-sync library. You can easily make your Live2D avatar open its mouth using audio files or even ndarrays output by AI models.<br>
Demo video.
[Demo video](https://www.bilibili.com/video/BV1nKGoeJEQY/?vd_source=49279a5158cf4b9566102c7e3806c231)<br>

- Provides capabilities in the form of a Python API for integration with other projects, leaving valuable computing resources for the avatar's "brain" rather than for audio capture software and virtual sound cards.
- Uses the Dynamic Time Warping (DTW) algorithm to match vowels in audio and outputs them via vowel confidence (softmax), rather than using AI models. Even mobile CPUs are more than sufficient.
- VTubeStudio is merely an optional Adapter for `pymouth`. You can use the [Low Level API](#low-level) to integrate with your desired avatar engine, using only the audio playback and analysis capabilities.

- The API has been fixed since version 1.3.0; please refer to this documentation.

## Quick Start

### Environment

- Python>=3.10
- VTubeStudio>=1.28.0 (Optional)

### Installation

```shell
pip install pymouth
```

### Get Started

1. Before starting, you need to turn on the Server switch in `VTubeStudio`. The port is usually 8001 by default.<br>
   ![server_start.png](https://github.com/organics2016/pymouth/blob/master/screenshot/server_start.png)
2. You need to determine the supported parameters for your Live2D lip-sync.<br>
   Please note: A simple judgment method is provided below, but this method will modify (reset) some lip-sync parameters of the Live2D model. Please back up your model before use.<br>
   If you know your model inside out, you can skip this step.<br>
   ![setup.png](https://github.com/organics2016/pymouth/blob/master/screenshot/setup.png)
    - After confirming the parameter reset, if the following information appears, it means your model only supports `Decibel-based lip-sync`.
      ![db.png](https://github.com/organics2016/pymouth/blob/master/screenshot/db.png)
    - After confirming the parameter reset, if the following information appears, it means your model only supports `Vowel-based lip-sync`.
      ![vowel.png](https://github.com/organics2016/pymouth/blob/master/screenshot/vowel.png)
    - If VTubeStudio finds all parameters and resets them successfully, it means both methods are supported. You only need to choose one method in the subsequent code.

3. Below are two demos based on different methods.<br>
   You can find an audio file to replace `some.wav`.<br>
   `samplerate`: The sampling rate of the audio data.<br>
   `output_device`: Output device Index. This is very important; if you don't tell the plugin which playback device to use, the plugin will not work properly.
   You can refer to [audio_devices_utils.py](https://github.com/organics2016/pymouth/blob/master/src/pymouth/audio_devices_utils.py)<br>
    - `Decibel-based lip-sync`
       ```python
       import time
       from pymouth import VTSAdapter, DBAnalyser
    
       def main():
         with VTSAdapter(DBAnalyser()) as a:
             a.action(audio='some.wav', samplerate=44100, output_device=2)
             time.sleep(100000)  # do something
    
    
       if __name__ == "__main__":
         main()
       ```

    - `Vowel-based lip-sync`
       ```python
       import time
       from pymouth import VTSAdapter, VowelAnalyser
    
       def main():
         with VTSAdapter(VowelAnalyser()) as a:
             a.action(audio='some.wav', samplerate=44100, output_device=2)
             time.sleep(100000)  # do something
    
    
       if __name__ == "__main__":
         main()
       ```

      When running the program for the first time, `VTubeStudio` will pop up a plugin authorization interface. After authorization, the plugin will generate a `pymouth_vts_token.txt` file in the runtime path.
      Subsequent runs will not require repeated authorization unless the token file is lost or authorization is removed in `VTubeStudio`.<br>

## About AI

Below is a relatively complete example of using pymouth as an AI TTS consumer.

```python
import queue
import threading
import time
from fish_speech import tts
from pymouth import VTSAdapter, DBAnalyser, VTSPluginInfo


class SpeakMsg:
    def __init__(self, msg: str, required: bool):
        self.msg = msg
        self.required = required
        self.create_timestamp = time.time()
        self.create_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.create_timestamp))


class Speaker:
    def __init__(self):
        self.queue = queue.Queue(1)

    def start(self):
        plugin_info = VTSPluginInfo(plugin_name='kanojyo2',
                                    developer='organics',
                                    authentication_token_path='./pymouth_vts_token.txt',
                                    plugin_icon=None)

        with VTSAdapter(DBAnalyser(temperature=10), plugin_info=plugin_info) as a:
            while True:
                msg: SpeakMsg = self.queue.get()
                t0 = time.time()
                audio, rate = tts.tts_ndarray(msg.msg)
                print(f'speak time:{time.time() - t0:.02f}')

                a.action(audio=audio, samplerate=rate, output_device=2)

    def speak(self, msg: str, required=True):
        if required:
            self.queue.put(SpeakMsg(msg, required))
        else:
            try:
                self.queue.put_nowait(SpeakMsg(msg, required))
            except queue.Full:
                print("Queue Full")


if __name__ == "__main__":
    speakers = Speaker()
    # 这里的实现只作为参考而不是建议。对于AI等CPU密集型场景，使用线程而不是协程可能会更好。
    threading.Thread(target=speakers.start).start()
```

## More Details

### High Level

There are only two key lines of code:

```python
with VTSAdapter(DBAnalyser(temperature=10)) as a:
    a.action(audio='some.wav', samplerate=44100, output_device=2)  # no-block
    # a.action_block(audio='aiueo.wav', samplerate=44100, output_device=2) # block
```

`temperature=10` Temperature (softmax).
Unlike the probability distribution for the next token in LLMs, the temperature here refers to the probability distribution of the similarity between each window frame FFT of the audio and the vowels. The larger the value, the more averaged the probability, and the mouth movement will become smoother. Vice versa. The default is 10, it cannot be `<=0`. You can adjust this value freely to observe the synchronization effect and determine the ideal value.<br>
`a.action()` is non-blocking and will return immediately, with the thread pool and queue maintained internally by the program.<br>
`a.action_block()` is blocking and will not return until the audio playback and processing are completed. It is pure synchronous code without internal threads; threads are maintained by the caller.<br>

`VTSAdapter` detailed parameter descriptions:

| param                   | required | default         | describe                                                 |
|:------------------------|:---------|:----------------|:---------------------------------------------------------|
| `analyser`              | Y        |                 | Analyser, must be a subclass of Analyser. Currently supports `DBAnalyser` and `VowelAnalyser`. |
| `db_vts_mouth_param`    |          | `'MouthOpen'`   | Only applies to `DBAnalyser`. The parameter in VTS that controls mouth_input. Please modify if it is not the default value. |
| `vowel_vts_mouth_param` |          | `dict[str,str]` | Only applies to `VowelAnalyser`. The parameter in VTS that controls mouth_input. Please modify if it is not the default value. |
| `ws_uri`                |          | `str`           | websocket uri. Default: ws://localhost:8001                     |
| `plugin_info`           |          | `VTSPluginInfo` | Plugin information, can be customized.                                               |

`a.action()` will start processing audio data. Detailed parameter descriptions:

| param               | required | default | describe                                                        |
|:--------------------|:---------|:--------|:----------------------------------------------------------------|
| `audio`             | Y        |         | Audio data. Can be a file path, a SoundFile object, or an ndarray.                    |
| `samplerate`        | Y        |         | Sampling rate. This depends on the sampling rate of the audio data. If you cannot obtain it, you can try the sampling rate of the output device. |
| `output_device`     | Y        |         | Output device Index. This depends on hardware or virtual devices. Use audio_devices_utils.py to print current system audio device information. |
| `finished_callback` |          | `None`  | This method will be called back when audio processing is completed.                                                  |
| `auto_play`         |          | `True`  | Whether to play audio automatically. Default is True, which plays audio (automatically writes audio to the specified `output_device`). |

### Low Level

Get Started demonstrates a High Level API. If you do not use `VTubeStudio` or want to use it more flexibly, you can try the Low Level API. Here is a demo.

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

- Test case

## Special Thanks

- Reference documents:
- [![](https://avatars.githubusercontent.com/u/1933673?s=40)卜卜口](https://github.com/itorr)
  https://github.com/itorr/itorr/issues/7
- https://www.zdaiot.com/DeepLearningApplications/%E8%AF%AD%E9%9F%B3%E5%90%88%E6%88%90/%E8%AF%AD%E9%9F%B3%E5%9F%BA%E7%A1%80%E7%9F%A5%E8%AF%86/
- https://huailiang.github.io/blog/2020/mouth/
- https://zh.wikipedia.org/wiki/%E5%85%B1%E6%8C%AF%E5%B3%B0
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pymouth)]()
[![PyPI - License](https://img.shields.io/pypi/l/pymouth)](https://github.com/organics2016/pymouth/blob/master/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/pymouth?color=green)](https://pypi.org/project/pymouth/)
[![PyPI Downloads](https://static.pepy.tech/badge/pymouth)](https://pepy.tech/projects/pymouth)

# pymouth

`pymouth` 是基于Python的Live2D口型同步库. 你可以用音频文件, 甚至是AI模型输出的ndarray,
就能轻松的让你的Live2D形象开口.<br>
效果演示视频.
[Demo video](https://www.bilibili.com/video/BV1nKGoeJEQY/?vd_source=49279a5158cf4b9566102c7e3806c231)<br>

- 以Python API的形式提供能力，用作和其他项目的集成，把宝贵的计算资源留给皮套的大脑，而不是给音频捕获软件和虚拟声卡。
- 采用动态时间规划算法(DTW)匹配音频中的元音，并以元音置信度(softmax)的方式输出，而不是使用AI模型，即使是移动端CPU也绰绰有余。
- VTubeStudio对`pymouth`来说只是可选项，只是一个Adapter，你可以使用[Low Level API](#low-level)和你想要皮套引擎结合，只使用音频播放和音频分析能力。

- 1.3.0版本之后API已固定，请以本文档为准。
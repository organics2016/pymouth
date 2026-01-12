[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pymouth)]()
[![PyPI - License](https://img.shields.io/pypi/l/pymouth)](https://github.com/organics2016/pymouth/blob/master/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/pymouth?color=green)](https://pypi.org/project/pymouth/)
[![PyPI Downloads](https://static.pepy.tech/badge/pymouth)](https://pepy.tech/projects/pymouth)

# pymouth

`pymouth` is a Python-based Live2D lip-sync library. You can easily make your Live2D avatar speak using audio files or even ndarrays output by AI models.<br>
Demo video.
[Demo video](https://www.bilibili.com/video/BV1nKGoeJEQY/?vd_source=49279a5158cf4b9566102c7e3806c231)<br>

- Provides capabilities in the form of a Python API for integration with other projects, leaving precious computing resources for the avatar's "brain" rather than audio capture software and virtual sound cards.
- Uses the Dynamic Time Warping (DTW) algorithm to match vowels in audio and outputs them as vowel confidence (softmax) instead of using AI models, making it more than sufficient even for mobile CPUs.
- VTubeStudio is just an option for `pymouth`, acting as an Adapter. You can use the [Low Level API](#low-level) to integrate with your desired avatar engine, utilizing only the audio playback and analysis capabilities.

- The API has been finalized since version 1.3.0; please refer to this documentation.
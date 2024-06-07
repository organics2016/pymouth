import audio2numpy
from audio2numpy import open_audio
from IPython.display import Audio
import pyaudio
import librosa
import audioread


def get_audio_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        # print(p.get_device_info_by_index(i).get('name'))
        devices.append(p.get_device_info_by_index(i))
    return devices


def get_audio_input_devices():
    devices = []
    for item in get_audio_devices():
        if item.get('maxInputChannels') > 0:
            devices.append(item)
    return devices


def get_audio_output_devices():
    devices = []
    for item in get_audio_devices():
        if item.get('maxOutputChannels') > 0:
            devices.append(item)
    return devices

if __name__ == '__main__':
    # get_audio_devices()
    print('输入设备:')
    for item in get_audio_input_devices():
        print(item)
    print('输出设备:')
    for item in get_audio_output_devices():
        print(item)

import threading
import time

from src.pymouth import VowelAnalyser


class Demo:
    def __init__(self):
        self.interrupt = False

    def __callback(self, md: dict[str, float], data):
        pass

    def __listening(self) -> bool:
        # Time-consuming operations are not recommended here.
        return self.interrupt

    def interrupt_handler(self):
        time.sleep(5) # do something
        print("interrupt")
        self.interrupt = True

    def boot(self):
        threading.Thread(target=self.interrupt_handler).start()

        with VowelAnalyser() as a:
            a.action_block('zh.wav', 44100,
                           output_device=3,
                           callback=self.__callback,
                           interrupt_listening=self.__listening)
            print("end")


Demo().boot()

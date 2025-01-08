# This script will calculate the percentage the average colors changed
# When the threshold of time has passed, during which the change percentage did not exceed a certain percentage: shutdown.

from ledstrip import LedStrip
import numpy as np
import time
from transmitter import Transmitter
from colorfactory import ColorFactory
import os


class PowerManager:
    def __init__(self, STANDBY_SECONDS: int, tr: Transmitter, cf: ColorFactory) -> None:
        self.STANDBY_SECONDS = STANDBY_SECONDS
        self.transmitter = tr
        self.color_factory = cf

        self.last_different = time.time()
        self.flattened_strips = np.array([])

    def is_idle(self, led_strips: list[LedStrip]) -> bool:
        is_idle = False
        new_image = False
        if len(self.flattened_strips) == 0:
            new_image = True
        else:
            change_percentage = (
                np.sum(np.abs(self.flattened_strips - self.flatten_strips(led_strips)))
                / (len(self.flattened_strips) * 255)
                * 100
            )
            # print(f"Change: {change_percentage} %")
            new_image = change_percentage > 0.1  # change larger than 1/10th of a percent

        if new_image:
            self.last_different = time.time()
        else:
            diff = time.time() - self.last_different
            print(f"Inactive time: {diff}")
            if diff >= self.STANDBY_SECONDS:
                print("POWER OFF")
                # self.shutdown() # full shutdown currently not used
                is_idle = True

        self.flattened_strips = self.flatten_strips(led_strips)

        return is_idle

    def flatten_strips(self, led_strips: list[LedStrip]) -> np.array:
        flattened_strips = np.array([])
        for strip in led_strips:
            flattened_strips = np.concatenate((flattened_strips, strip.colors.copy().flatten()))
        return flattened_strips

    def shutdown(self) -> None:
        # While statements are used because the no_acknowledge feature is turned on and some packages can go lost
        for _ in range(0, 20):
            now = time.time()
            strips = self.color_factory.set_strips(np.array([0, 0, 255]))
            while time.time() - now <= 0.5:
                self.transmitter.update_receivers(strips)
            now = time.time()
            strips = self.color_factory.set_strips(np.array([0, 0, 0]))
            while time.time() - now <= 0.5:
                self.transmitter.update_receivers(strips)

        os.system("sudo shutdown now")

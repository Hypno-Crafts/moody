# This class represents a LED strip and controls all its pixel colors.

import numpy as np


class LedStrip:
    def __init__(self, id: int, led_count: int) -> None:
        """
        Initialize the LED strip.

        Args:
            id (int): Identifier for the LED strip. Must be unique! Map this on the id set on each Arduino
            led_count (int): Number of LEDs in the strip.
        """
        self.id = id
        self.led_count = led_count
        self.colors = np.zeros((led_count, 3))  # Default color is off (black).

        self.color_test_index = 0
        self.color_cycle = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]])

    def update_light(self, index: id, color: np.ndarray) -> None:
        """
        Update the color of a specific LED.

        Args:
            index (int): Index of the LED to update.
            color (np.ndarray): RGB color array for the LED.
        """
        self.colors[index] = color

    def set_next_color(self) -> None:
        """
        Set all LEDs to the same color, cycling through colors.
        """
        current_color = self.color_cycle[self.color_test_index]
        self.colors[:] = current_color
        self.color_test_index = (self.color_test_index + 1) % 3

    def set_lights(self, color: np.array) -> None:
        self.colors[:] = color

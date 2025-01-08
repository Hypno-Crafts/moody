# This class is responsible for analizing the pixel colors and calculate the colors to broadcast.
# It also contains the LedStrips objects and can return, read and write their colors.
# The horizontal_count indicates the amount of average colors to calculate for the top and bottom border of the screen.
# The vertical_count indicates the amount of average colors to calculate for the left and right border of the screen.

import numpy as np
import cv2
from ledstrip import LedStrip


class ColorFactory:
    # only used for debugging purposes, will draw the average colors but will slow down the average FPS
    draw_squares = False

    def __init__(self, horizontal_count: int, vertical_count: int):
        self.horizontal_count = horizontal_count
        self.vertical_count = vertical_count

        # don't change these id's
        self.led_strips = {
            "left": LedStrip(1, vertical_count),
            "top": LedStrip(2, horizontal_count),
            "right": LedStrip(3, vertical_count),
            "bottom": LedStrip(4, horizontal_count),
            "full_screen": LedStrip(5, 1),
        }
        ids = [self.led_strips[k].id for k in self.led_strips.keys()]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Every id of each LedStrip must be unique.")
        elif 0 in ids:
            raise ValueError(f"Id '0' cannot be used for initiating a LedStrip. It's reserved for the transmitter.")

    def get_average_color(self, x: int, y: float, h_size: int, v_size: int, image: np.ndarray) -> np.ndarray:
        # Define square's start and end points
        start_point = (int(x - v_size / 2), int(y - h_size / 2))
        end_point = (int(x + v_size / 2), int(y + h_size / 2))
        # Ensure the region is within the image bounds
        start_point = (max(start_point[0], 0), max(start_point[1], 0))
        end_point = (min(end_point[0], image.shape[1]), min(end_point[1], image.shape[0]))

        # Calculate the average color in this region from the original image
        region = image[start_point[1] : end_point[1], start_point[0] : end_point[0]]

        if region.size > 0:  # Avoid empty regions
            average_color = region.mean(axis=(0, 1)).astype(int)
        else:
            average_color = np.zeros((1, 3))  # Fallback if region is empty

        if ColorFactory.draw_squares:
            cv2.rectangle(image, start_point, end_point, tuple(map(int, average_color)), -1)

        # Return the average color
        return average_color

    def calculate_colors(self, image: np.ndarray) -> tuple[np.ndarray, list[LedStrip]]:
        image = cv2.resize(image, (100, 100), interpolation=cv2.INTER_AREA)
        height, width = image.shape[:2]

        square_size_horizontal = int(width / self.horizontal_count)
        square_size_vertical = int(height / self.vertical_count)

        for index, i in enumerate(
            np.linspace(square_size_horizontal / 2, width - square_size_horizontal / 2, self.horizontal_count)
        ):
            x = int(i)

            c = self.get_average_color(x, square_size_horizontal / 2, int(height / 2), square_size_horizontal, image)
            self.led_strips["top"].update_light(index, c)

            c = self.get_average_color(
                x, height - square_size_horizontal / 2, int(height / 2), square_size_horizontal, image
            )
            self.led_strips["bottom"].update_light(index, c)

        for index, i in enumerate(
            np.linspace(square_size_vertical / 2, height - square_size_vertical / 2, self.vertical_count)
        ):
            y = int(i)

            c = self.get_average_color(square_size_vertical / 2, y, square_size_vertical, int(width / 2), image)
            self.led_strips["left"].update_light(index, c)

            c = self.get_average_color(width - square_size_vertical / 2, y, square_size_vertical, int(width / 2), image)
            self.led_strips["right"].update_light(index, c)

        self.led_strips["full_screen"].update_light(0, image.mean(axis=(0, 1)).astype(int))

        return image, self.get_strips()

    def get_strips(self) -> list[LedStrip]:
        return [
            self.led_strips["left"],
            self.led_strips["right"],
            self.led_strips["top"],
            self.led_strips["bottom"],
            self.led_strips["full_screen"],
        ]

    def test_strips(self) -> list[LedStrip]:
        for strip in self.get_strips():
            strip.set_next_color()
        return self.get_strips()

    def set_strips(self, color: np.array) -> list[LedStrip]:
        for strip in self.get_strips():
            strip.set_lights(color)
        return self.get_strips()

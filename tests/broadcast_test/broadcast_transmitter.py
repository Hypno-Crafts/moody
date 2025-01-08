# Do not change any parameters in this test script if you are not sure what they do.
# This code will light up exactly 5 LEDs on the transmitter for a specified duration, changing their color every time.
# It ends after 5 seconds.
# (rotating between red, green and blue)

import argparse
import time
from transmitter import Transmitter
from colorfactory import ColorFactory
import configparser
import numpy as np

config = configparser.ConfigParser()
config.read("config.ini")

COLORS_IN_PAYLOAD = config.getint("parameters", "COLORS_IN_PAYLOAD")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=5, help="Duration in seconds.")
    commandlineargs = parser.parse_args()
    duration = commandlineargs.duration
    print(f"Duration = {duration}")

    LED_COUNT = 5  # Hardcoded 5, do not change in this test file
    INTERVAL = 1000 / 3

    color_factory = ColorFactory(LED_COUNT, LED_COUNT)  # Hardcoded to just test 5 lights
    transmitter = Transmitter(COLORS_IN_PAYLOAD)

    # Start the timer
    start_time = time.time()
    elapsed_time = time.time() - start_time

    try:
        while elapsed_time <= duration:
            now = int(time.monotonic_ns() / 1000000)

            now = time.time()
            strips = color_factory.test_strips()
            # While statements is used because the no_acknowledge feature is turned on and some packages can go lost
            while time.time() - now <= INTERVAL / 1000:
                transmitter.update_receivers(strips)
            elapsed_time = time.time() - start_time

    except KeyboardInterrupt:
        print("powering down radio and exiting.")
        strips = color_factory.set_strips(np.array([0, 0, 0]))
        transmitter.update_receivers(strips)
        transmitter.close()

    print("powering down radio and exiting.")
    strips = color_factory.set_strips(np.array([0, 0, 0]))
    transmitter.update_receivers(strips)
    transmitter.close()

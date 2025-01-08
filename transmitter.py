"""
Based on https://nRF24.github.io/pyRF24
"""

# This script will broadcast the average colors to the arduino's
# Adding an id and offset to indicate who should receive the data and from where to start updating colors.
# Suppose that the COLORS_IN_PAYLOAD is 10, then the payload will be exactly 10 colors. 
# If the horizontal_count is set on 25, the broadcaster will have to split that over 3 payloads for the same id, with 3 different offsets.
# The Arduino's will act upon these ids and offsets and only update the relevant pixels on the LED strips.

import struct
from pyrf24 import RF24, RF24_DRIVER, RF24_1MBPS, RF24_2MBPS, RF24_250KBPS, RF24_PA_HIGH, RF24_PA_LOW
from ledstrip import LedStrip


class Transmitter:
    def __init__(self, COLORS_IN_PAYLOAD: int) -> None:
        self.COLORS_IN_PAYLOAD = COLORS_IN_PAYLOAD

        ########### USER CONFIGURATION ###########
        # CE Pin uses GPIO number with RPi and SPIDEV drivers, other drivers use
        # their own pin numbering
        # CS Pin corresponds the SPI bus number at /dev/spidev<a>.<b>
        # ie: radio = RF24(<ce_pin>, <a>*10+<b>)
        # where CS pin for /dev/spidev1.0 is 10, /dev/spidev1.1 is 11 etc...
        CSN_PIN = 0  # aka CE0 on SPI bus 0: /dev/spidev0.0
        if RF24_DRIVER == "MRAA":
            CE_PIN = 15  # for GPIO22
        elif RF24_DRIVER == "wiringPi":
            CE_PIN = 3  # for GPIO22
        else:
            CE_PIN = 22
        self.radio = RF24(CE_PIN, CSN_PIN)

        # initialize the nRF24L01 on the spi bus
        if not self.radio.begin():
            raise OSError("nRF24L01 hardware isn't responding")

        # Configure radio
        self.radio.setAutoAck(False)  # Disable acknowledgment
        self.radio.channel = 90  # Set communication channel
        self.radio.setDataRate(RF24_2MBPS)  # Set data rate
        self.radio.openWritingPipe(0xF0F0F0F0E1)  # Use a broadcast address
        self.radio.setPALevel(RF24_PA_HIGH)  # Power level: low for closer range, high for further range

        self.radio.print_pretty_details()

    def create_payload(self, id, offset, colors) -> bytes:
        color_data = colors.flatten().tolist()  # Flatten the (x, 3) array to 1D

        if len(color_data) < self.COLORS_IN_PAYLOAD * 3:
            color_data.extend([0] * (self.COLORS_IN_PAYLOAD * 3 - len(color_data)))

        payload_integers = [id, offset] + [int(value) for value in color_data]

        # Pack the data as integers into byte format
        return struct.pack(f"{len(payload_integers)}B", *payload_integers)

    def send_colors_in_chunks(self, colors, id) -> None:
        total_colors = colors.shape[0]

        for offset in range(0, total_colors, self.COLORS_IN_PAYLOAD):
            chunk = colors[offset : offset + self.COLORS_IN_PAYLOAD]
            payload_data = self.create_payload(id, offset, chunk)

            # Send the payload
            self.radio.write(payload_data, multicast=True)

    def update_receivers(self, led_strips: list[LedStrip]) -> None:
        for strip in led_strips:
            self.send_colors_in_chunks(strip.colors, id=strip.id)

    def close(self) -> None:
        self.radio.power = False

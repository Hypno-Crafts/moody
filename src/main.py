# This is the main script, it will read the HDMI input stream, calculate average colors, and send it to the LED strip

import cv2
import argparse
import time
from colorfactory import ColorFactory
from transmitter import Transmitter
from powermanager import PowerManager
from pathlib import Path
import configparser
import numpy as np

config = configparser.ConfigParser()
config.read("config.ini")

COLORS_IN_PAYLOAD = config.getint("parameters", "COLORS_IN_PAYLOAD")
HORIZONTAL_LEDS = config.getint("parameters", "HORIZONTAL_LEDS")
VERTICAL_LEDS = config.getint("parameters", "VERTICAL_LEDS")
STANDBY_SECONDS = config.getint("parameters", "STANDBY_SECONDS")
MODE = config.get("parameters", "MODE")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="Set this flag to record video")
    parser.add_argument("--file", action="store_true", help="Use local video file instead of videostream")
    parser.add_argument("--preview", action="store_true", help="Show preview")
    parser.add_argument("--dark", action="store_true", help="No data broadcasting")
    parser.add_argument("--duration", type=int, default=-1, help="Duration in seconds")
    commandlineargs = parser.parse_args()

    # Initialize color factory
    color_factory = ColorFactory(HORIZONTAL_LEDS, VERTICAL_LEDS, MODE)

    if not commandlineargs.dark:
        print("Broadcasting data enabled")
        # Initialize transmitter and power manager
        transmitter = Transmitter(COLORS_IN_PAYLOAD)
        pm = PowerManager(STANDBY_SECONDS, transmitter, color_factory)
    else:
        print("Broadcasting data disabled")

    # Define the recording duration
    duration = commandlineargs.duration

    if commandlineargs.file:
        print(f"Processing 'video.mp4'")
        current_path = Path.cwd()
        # Stream local video file
        vc = cv2.VideoCapture(str(current_path / "video.mp4"))
    else:
        # Stream local HDMI video captured with HDMI to USB device
        print("Processing HDMI data")
        vc = cv2.VideoCapture(0)
        if MODE == "AVERAGE":
            vc.set(cv2.CAP_PROP_FRAME_WIDTH, 480) # leave on 480 for the YOLO models
            vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # leave on 480 for the YOLO models

    if not vc.isOpened() and not commandlineargs.dark:
        print("Error: Could not open video stream.")
        # Blink 5 LEDs in blue color to indicate this error.
        for _ in range(0, 10):
            now = time.time()
            strips = color_factory.set_strips(np.array([255, 0, 0]))
            while time.time() - now <= 0.5:
                transmitter.update_receivers(strips)
            now = time.time()
            strips = color_factory.set_strips(np.array([0, 0, 0]))
            while time.time() - now <= 0.5:
                transmitter.update_receivers(strips)
        exit()

    # Get frame properties for recording
    frame_width = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Set up video writer if recording
    if commandlineargs.record:
        fourcc = cv2.VideoWriter_fourcc(*"MP4V")  # Use 'XVID' or 'MJPG' for .avi, 'MP4V' for .mp4
        out = cv2.VideoWriter("video.mp4", fourcc, 20.0, (frame_width, frame_height))
        print(f"Recording video to 'video.mp4'")

    if commandlineargs.preview:
        print(f"Previewing enabled")

    if duration > 0:
        print(f"Running for {duration} seconds...")
    else:
        if not commandlineargs.file:
            print("Duration: INFINITY")

    # Start the timer
    start_time = time.time()
    last_print_time = start_time  # Time of the last FPS print
    frame_count = 0  # Number of frames processed

    is_idle = False
    while True:
        rval, frame = vc.read()
        if not rval:
            break
        frame_with_squares, led_strips = color_factory.calculate_colors(frame)

        # Record the frame if recording is enabled
        if commandlineargs.record:
            out.write(frame_with_squares)
        elif commandlineargs.preview:
            # Preview the frame if not recording
            cv2.imshow("preview", frame_with_squares)

        # Increment frame count
        frame_count += 1

        # Check if seconds have passed for printing FPS
        elapsed_time = time.time() - last_print_time

        if elapsed_time >= 5:  # Print FPS every 5 seconds
            fps = frame_count / elapsed_time  # Calculate FPS

            if not commandlineargs.dark:
                # check to power down after certain time of inactivity
                is_idle = pm.is_idle(led_strips)
                print(f"Idle status: {is_idle}")

            print(f"FPS: {fps:.2f}")

            # Reset counters
            last_print_time = time.time()
            frame_count = 0

        # Do not transmit colours when idle
        if not commandlineargs.dark and not is_idle:
            transmitter.update_receivers(led_strips)

        # Check if seconds have passed
        total_elapsed_time = time.time() - start_time
        if total_elapsed_time > duration and duration >= 0:
            print("Finished.")
            break

        # Check for ESC key to stop early
        if cv2.waitKey(20) == 27:  # ESC key to exit
            print("Recording stopped by user.")
            break

    # Release resources
    if not commandlineargs.dark:
        transmitter.close()
    vc.release()
    if commandlineargs.record:
        out.release()
    cv2.destroyAllWindows()

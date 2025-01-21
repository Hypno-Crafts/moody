# this script serves debugging purposes only
# it creates a .mp4 file which can be used instead of the HDMI to USB capture device

import cv2
import numpy as np
import argparse
from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=5, help="Duration in seconds")
    commandlineargs = parser.parse_args()

    # Video settings
    width, height = 1920, 1080
    fps = 30
    duration = commandlineargs.duration
    num_frames = duration * fps
    frames_per_quarter = fps  # Show each color for 1 second (20 frames)

    # Initialize Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("video.mp4", fourcc, fps, (width, height))

    # Loop through frames, alternating the color between quarters
    for frame_idx in tqdm(range(num_frames)):
        # Create a blank (black) frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Determine which quarter to color
        active_quarter = (frame_idx // frames_per_quarter) % 4

        # Assign the random color to the specified active quarter
        if active_quarter == 0:
            frame[: height // 2, : width // 2] = (255, 0, 0)
        elif active_quarter == 1:
            frame[: height // 2, width // 2 :] = (0, 255, 0)
        elif active_quarter == 3:
            frame[height // 2 :, : width // 2] = (255, 255, 255)
        elif active_quarter == 2:
            frame[height // 2 :, width // 2 :] = (0, 0, 255)

        # Write frame to video file
        out.write(frame)

    # Release resources
    out.release()
    cv2.destroyAllWindows()

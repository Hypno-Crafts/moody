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

    # Initialize Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter("video.mp4", fourcc, fps, (width, height))

    # Define the pie chart segments with rainbow colors
    colors = [
        (148, 0, 211),  # Violet
        (138, 43, 226),  # Blue Violet
        (123, 104, 238),  # Medium Slate Blue
        (75, 0, 130),  # Indigo
        (72, 61, 139),  # Dark Slate Blue
        (106, 90, 205),  # Slate Blue
        (0, 0, 255),  # Blue
        (0, 191, 255),  # Deep Sky Blue
        (0, 255, 255),  # Cyan
        (0, 255, 127),  # Spring Green
        (0, 255, 0),  # Green
        (127, 255, 0),  # Chartreuse
        (173, 255, 47),  # Green Yellow
        (255, 255, 0),  # Yellow
        (255, 215, 0),  # Gold
        (255, 165, 0),  # Orange
        (255, 140, 0),  # Dark Orange
        (255, 69, 0),  # Red Orange
        (255, 0, 0),  # Red
        (255, 20, 147),  # Deep Pink
        (255, 105, 180),  # Hot Pink
        (255, 182, 193),  # Light Pink
        (255, 0, 255),  # Magenta
        (238, 130, 238),  # Violet Red
    ]

    num_segments = len(colors)
    angle_per_segment = 360 // num_segments

    # Center of the pie and size
    center = (width // 2, height // 2)
    radius = int(min(width, height) * 1.1)

    # Generate frames with rotating pie chart
    for frame_idx in tqdm(range(num_frames)):
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Calculate rotation angle for this frame
        rotation_angle = (frame_idx * 360 / num_frames) % 360

        # Draw each segment of the pie chart with rotation
        for i, color in enumerate(colors):
            # Calculate start and end angle for each segment
            start_angle = i * angle_per_segment + rotation_angle
            end_angle = start_angle + angle_per_segment

            # Draw segment
            cv2.ellipse(
                frame, center, (radius, radius), 0, start_angle, end_angle, color, thickness=-1
            )  # Filled pie slice

        # Write frame to video file
        out.write(frame)

    # Release resources
    out.release()
    cv2.destroyAllWindows()

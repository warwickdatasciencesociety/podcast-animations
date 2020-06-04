"""Generate an animation of the cellular automaton Rule 30."""

import os
import pathlib
import shutil
import subprocess
import tempfile

import colour
import cv2
import imageio
import numpy as np
import scipy.signal as sg
import tqdm

# Parameters
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
SECS = int(60 * 1)
FPS = 30
PIXEL_SIZE = 5
OUTPUT_PATH = 'rule_30.mp4'
FFMPEG_PATH = '/usr/bin/ffmpeg'

# Constants
STATE_WIDTH = VIDEO_WIDTH // PIXEL_SIZE
STATE_HEIGHT = VIDEO_HEIGHT // PIXEL_SIZE
NUM_FRAMES = SECS * FPS


class Rule30:
    """A class for running Rule 30."""

    neighbours = np.array([[1, 2, 4]], np.uint8)
    kernel = np.array([0, 1, 1, 1, 1, 0, 0, 0])
    colours = np.array([[0, 0, 0], [255, 255, 255]], np.uint8)

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.state = np.zeros((self.height, self.width), np.uint8)
        self.peak_height = 1
        self.state[-1, self.width // 2] = 1

        self.rgb = None
        self._update_rgb()

    def step(self):
        self._update_state()
        self._update_rgb()
    
    def _update_state(self):
        rule_index = sg.convolve2d(self.state, self.neighbours,
                                   mode='same', boundary='wrap')
        self.state = self.kernel[rule_index]

        if self.peak_height < self.height:
            self.peak_height += 1
            self.state[-self.peak_height, self.width // 2] = 1

    def _update_rgb(self):
        self.rgb = self.colours[self.state]

class VideoConverter:
    """A class for converting frames of NumPy arrays to a video."""

    def __init__(self, fps=30):
        """Initialise the converter and create a temporary directory.

        Args:
            fps (int): Frames per second for the converted video
        """
        self.fps = fps
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.curr_frame = 0

    def add_frame(self, frame):
        """Adds a new frame to the video.

        Args:
            frame (uint8 NumPy array of shape: (video_height, video_width, 3))
                Data of the new frame as RGB. All frames must have the same
                dimensions.
        """
        frame_path = os.path.join(self.tmp_dir.name, f'{self.curr_frame}.png')
        imageio.imwrite(frame_path, frame)
        self.curr_frame += 1

    def write(self, output_path):
        """Converts the accumulated frames to video and writes the result.

        Args:
            output_path: (string) Path where to save the video file
        """
        abs_tmp_dir_path = pathlib.Path(self.tmp_dir.name).absolute()
        abs_output_path = pathlib.Path(output_path).absolute()
        os.makedirs(os.path.dirname(abs_output_path), exist_ok=True)
        subprocess.call([FFMPEG_PATH,
                         '-framerate', f'{self.fps}',
                         '-i', f'{abs_tmp_dir_path}/%d.png',
                         '-vcodec', 'libx264',
                         '-pix_fmt', 'yuv420p',
                         # Video quality, lower is better, but zero (lossless)
                         # doesn't work.
                         '-crf', '1',
                         '-y',  # overwrite output files without asking
                         abs_output_path
                         ])
        self.tmp_dir.cleanup()
        print(f"Video written to: {abs_output_path}")


def main():
    converter = VideoConverter(fps=FPS)
    animation = Rule30(STATE_WIDTH, STATE_HEIGHT)

    for __ in tqdm.trange(NUM_FRAMES):
        small_frame = animation.rgb
        enlarged_frame = cv2.resize(small_frame, (VIDEO_WIDTH, VIDEO_HEIGHT),
                                    interpolation=cv2.INTER_NEAREST)
        converter.add_frame(enlarged_frame)
        animation.step()

    converter.write(OUTPUT_PATH)


if __name__ == '__main__':
    main()
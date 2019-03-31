import logging
import subprocess
import threading
import time
import wave
from datetime import datetime
from queue import Queue
from typing import List, Tuple

import cv2
import pyaudio
from numpy.core.multiarray import ndarray

from Constants import Constants


class SaveManager(threading.Thread):
    """
    Class that manages the process to save a video (so mixing the audio with the video, adding
    data to the images, etc).
    """

    def __init__(self, save_triggered: Queue, camera_data: Queue, audio_data: Queue):
        super().__init__()
        self.audio_data = audio_data
        self.camera_data = camera_data
        self.logger = logging.getLogger('main.saveManager')
        self.save_trigger = save_triggered  # Used to tell the thread to save a video.

    def run(self):
        self.logger.debug("SaveManager thread started")
        while True:
            self.save_trigger.get()  # wait until a save is requested...
            self.save()

    def save(self):
        self.logger.info("Save requested")
        camera_data = self.camera_data.get()
        audio_data = self.audio_data.get()
        self.write_camera_to_disk(camera_data)
        self.write_audio_to_disk(audio_data)
        self.merge_audio_and_video()

    def write_camera_to_disk(self, frames):
        self.logger.debug("Writing camera to disk")
        video_dimension = frames[0][1].shape[1], frames[0][1].shape[0]
        self.add_timestamp_to_frames(frames, video_dimension)
        average_frames_per_seconds = len(frames) / (frames[len(frames) - 1][0] - frames[0][0])
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(f'{Constants.TEMP_FOLDER}{Constants.VIDEO_FILE}', fourcc, average_frames_per_seconds, video_dimension)
        for timestamp, image  in frames:
            out.write(image)
        out.release()
        self.logger.debug("Camera video has been written")

    def write_audio_to_disk(self, frames):
        self.logger.debug("Saving microphone data to disk")
        wf = wave.open(f'{Constants.TEMP_FOLDER}{Constants.AUDIO_FILE}', 'wb')
        wf.setnchannels(Constants.CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(Constants.FORMAT))
        wf.setframerate(Constants.SAMPLE_RATE)
        for timestamp, frame in frames:
            wf.writeframes(frame)
        wf.close()

    def add_timestamp_to_frames(self, frames: List[Tuple[float, ndarray]], video_dimension: Tuple[int, int]):
        """
            Adds a small timestamp to the bottom-right of frames.
            :param video_dimension: Image dimensions in pixels ex: (1920, 1080)
            :param frames: list of tuples containing timestamp, frame
        """
        BOTTOM_OFFSET = 10
        RIGHT_OFFSET = 10
        RECTANGLE_HEIGHT = 20
        RECTANGLE_WIDTH = 165
        width, height = video_dimension
        for timestamp, frame in frames:
            background_color = (0, 0, 0)
            cv2.rectangle(frame,
                          (width - RECTANGLE_WIDTH - RIGHT_OFFSET, height - RECTANGLE_HEIGHT),
                          (width - RIGHT_OFFSET,
                           height - BOTTOM_OFFSET),
                          background_color, thickness=-1)
            readable_datetime = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
            cv2.putText(frame, readable_datetime,
                        (width - RECTANGLE_WIDTH - RIGHT_OFFSET,
                         height - BOTTOM_OFFSET),
                        fontFace=2, fontScale=0.45, color=(255, 255, 255))

    def merge_audio_and_video(self):
        self.logger.debug("Mixing audio and video")
        subprocess.run('ffmpeg -y -v 0 -i {0} -i {1} -c:v copy '
                       '-c:a aac -strict experimental {2}'
                       .format(Constants.TEMP_FOLDER + Constants.VIDEO_FILE,
                               Constants.TEMP_FOLDER + Constants.AUDIO_FILE,
                               Constants.SAVE_FOLDER + f"recording_{time.time()}.avi"))
        self.logger.debug("Mixing audio and video DONE")

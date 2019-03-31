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

    def __init__(self, save_triggered: Queue, camera_data: Queue, audio_data: Queue, car_data: Queue):
        super().__init__()
        self.car_data = car_data
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
        car_data = self.car_data.get()
        if len(camera_data) > 0:
            self.write_camera_to_disk(camera_data, car_data)
            self.write_audio_to_disk(audio_data)
            self.merge_audio_and_video()

    def write_camera_to_disk(self, frames, car_data):
        self.logger.debug("Writing camera to disk")
        video_dimension = frames[0][1].shape[1], frames[0][1].shape[0]
        self.add_timestamp_to_frames(frames, video_dimension)
        self.add_car_data_to_frames(frames, car_data, video_dimension)
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
            readable_datetime = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
            self.paint(BOTTOM_OFFSET, width - RIGHT_OFFSET - RECTANGLE_WIDTH, RECTANGLE_HEIGHT, RECTANGLE_WIDTH,
                       frame, width, height, readable_datetime)

    def merge_audio_and_video(self):
        self.logger.debug("Mixing audio and video")
        subprocess.run('ffmpeg -y -v 0 -i {0} -i {1} -c:v copy '
                       '-c:a aac -strict experimental {2}'
                       .format(Constants.TEMP_FOLDER + Constants.VIDEO_FILE,
                               Constants.TEMP_FOLDER + Constants.AUDIO_FILE,
                               Constants.SAVE_FOLDER + f"recording_{time.time()}.avi"))
        self.logger.debug("Mixing audio and video DONE")

    def add_car_data_to_frames(self, frames, car_data, video_dimension):
        RECTANGLE_HEIGHT = 20
        width, height = video_dimension
        normalized_data = {}
        for timestamp, data in car_data:
            normalized_data[round(timestamp)] = data
        rpm = "RPM: N/A"
        kmh = "N/A km/h"
        runtime = "Up: N/A sec"
        fuel_level = "Fuel: N/A%"
        accelerator_level = "Acc: N/A%"
        check_engine_on = "ChkEng: ?"
        for timestamp, frame in frames:
            rounded_timestamp = round(timestamp)
            if rounded_timestamp in normalized_data:
                rpm = f"RPM: {normalized_data[rounded_timestamp]['rpm']}"
                kmh = f"{normalized_data[rounded_timestamp]['kmh']} km/h"
                runtime = f"Up: {normalized_data[rounded_timestamp]['runtime']} sec"
                fuel_level = f"Fuel: {round(normalized_data[rounded_timestamp]['fuel_level'], 2)}%"
                accelerator_level = f"Acc: {round(normalized_data[rounded_timestamp]['accelerator_pos'], 2)}%"
                check_engine_on = f"ChkEng: {'on' if normalized_data[rounded_timestamp]['check_engine_on'] != 0 else 'off'}"
            self.paint(text=rpm, bottom_offset=10, left_offset=10, rectangle_height=RECTANGLE_HEIGHT, rectangle_width=100,
                       frame=frame, frame_width=width, frame_height=height)
            self.paint(text=kmh, bottom_offset=30, left_offset=10, rectangle_height=RECTANGLE_HEIGHT,
                       rectangle_width=100,
                       frame=frame, frame_width=width, frame_height=height)
            self.paint(text=runtime, bottom_offset=50, left_offset=10, rectangle_height=RECTANGLE_HEIGHT,
                       rectangle_width=100,
                       frame=frame, frame_width=width, frame_height=height)
            self.paint(text=fuel_level, bottom_offset=10, left_offset=110, rectangle_height=RECTANGLE_HEIGHT,
                       rectangle_width=100,
                       frame=frame, frame_width=width, frame_height=height)
            self.paint(text=accelerator_level, bottom_offset=10, left_offset=210, rectangle_height=RECTANGLE_HEIGHT,
                       rectangle_width=100,
                       frame=frame, frame_width=width, frame_height=height)
            self.paint(text=check_engine_on, bottom_offset=30, left_offset=110, rectangle_height=RECTANGLE_HEIGHT,
                       rectangle_width=100,
                       frame=frame, frame_width=width, frame_height=height)

    def paint(self, bottom_offset: int, left_offset: int, rectangle_height: int,
              rectangle_width: int, frame: ndarray, frame_width: int, frame_height: int, text: str):
        background_color = (0, 0, 0)
        cv2.rectangle(frame,
                      (left_offset, frame_height - rectangle_height - bottom_offset),
                      (left_offset + rectangle_width,
                       frame_height - bottom_offset),
                      background_color, thickness=-1)
        cv2.putText(frame, text,
                    (left_offset,
                     frame_height - bottom_offset),
                    fontFace=2, fontScale=0.45, color=(255, 255, 255))

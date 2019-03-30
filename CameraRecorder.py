import logging
import threading
import time
from collections import deque
from queue import Queue

import cv2

from Recorder import Recorder


class CameraRecorder(Recorder, threading.Thread):
    """
    Thread that fetches camera's content.
    """

    def __init__(self, capture_duration: int):
        threading.Thread.__init__(self)
        Recorder.__init__(self, capture_duration)
        self.logger = logging.getLogger('main.camera')

    def run(self):
        self.logger.debug("Starting camera thread.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise IOError("Cannot open webcam")
        while self.continue_running:
            pass
            _, frame = cap.read()
            current_time = time.time()
            self.remove_old_frames(current_time)
            self.queue.append((current_time, frame))
            # cv2.imshow('frame',frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
            self.logger.info(len(self.queue))
        cap.release()
        self.write_to_disk()
        self.logger.debug("Camera thread stopped")

    def write_to_disk(self):
        self.logger.debug("Writing to disk")
        frames = self.queue.copy()
        self.queue.clear()
        average_frames_per_seconds = len(frames) / (frames[len(frames) - 1][0] - frames[0][0])
        video_dimension = frames[0][1].shape[1], frames[0][1].shape[0]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter('temp/camera_recorder.avi', fourcc, average_frames_per_seconds, video_dimension)
        for timestamp, image in frames:
            out.write(image)
        out.release()
        self.logger.debug("Camera video has been written")


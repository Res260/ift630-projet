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
        self.logger.debug("Camera thread stopped")


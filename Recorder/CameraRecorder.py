import logging
import threading
import time
from queue import Queue

import cv2
import numpy as np

from Recorder.Recorder import Recorder


class CameraRecorder(Recorder, threading.Thread):
    """
    Thread that fetches camera's content.
    """

    def __init__(self, capture_duration: int, camera_data: Queue):
        threading.Thread.__init__(self)
        Recorder.__init__(self, capture_duration)
        self.camera_data = camera_data
        self.logger = logging.getLogger('main.camera')

    def run(self):
        self.logger.debug("Starting camera thread.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise IOError("Cannot open webcam")
        _, frame = cap.read()  # Read a dummy frame so opencv is faster on the subsequent reads (idk why its needed but it is)
        self.logger.debug("Camera ready")
        self.ready = True
        self.wait_to_start()

        while self.continue_running:
            _, frame = cap.read()
            last_frame = None
            current_time = time.time()
            # if len(self.queue) > 0:
            if not np.array_equal(frame, last_frame):
                last_frame = frame
                self.remove_old_frames(current_time)
                # We poll images a t X frames per seconds, but the camera refresh rate might be lower.
                self.queue.append((current_time, frame))

        cap.release()
        self.camera_data.put(self.queue.copy())
        self.logger.debug("Camera thread stopped")


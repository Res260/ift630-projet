import logging
import threading
import time
from collections import deque
from queue import Queue

import cv2


class CameraThread(threading.Thread):
    """
    Thread that fetches camera's content.
    """

    def __init__(self, capture_duration: int):
        super().__init__()
        self.capture_duration = capture_duration
        self.logger = logging.getLogger('main.camera')
        self.queue = deque()
        self.continue_running = True

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

    def remove_old_frames(self, current_time):
        if len(self.queue) > 0:
            continue_popping = True
            while continue_popping:
                if current_time - self.queue[0][0] > self.capture_duration:
                    # remove last frames
                    self.queue.popleft()
                else:
                    continue_popping = False


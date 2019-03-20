import logging
import threading
import time
from queue import Queue

import cv2


class CameraThread(threading.Thread):
    """
    Thread that fetches camera's content.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('main.camera')
        self.queue = Queue()
        self.continue_running = True

    def run(self):
        self.logger.debug("Starting camera thread.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise IOError("Cannot open webcam")
        while self.continue_running:
            pass
            _, frame = cap.read()
            self.queue.put(frame)
            # cv2.imshow('frame',frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
        cap.release()
        self.logger.debug("Camera thread stopped")


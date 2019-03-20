import signal
import logging
import os
import time

from CameraThread import CameraThread


class App:
    def __init__(self):
        self.logger = logging.getLogger('main')
        self.prepare_logger()
        self.camera_thread = CameraThread()

    def prepare_logger(self):
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())
        os.makedirs('log', exist_ok=True)
        self.logger.addHandler(logging.FileHandler('log/shadowCar.log'))

    def run(self):
        self.camera_thread.start()
        self.logger.info("ahah")
        while self.camera_thread.continue_running:
            # This is needed since thread.join() blocks signals...
            time.sleep(1)
        self.camera_thread.join()

    def trigger(self, signum, frame):
        self.logger.info("Triggered")
        self.camera_thread.continue_running = False


if __name__ == "__main__":
    app = App()
    signal.signal(signal.SIGINT, app.trigger)
    app.run()

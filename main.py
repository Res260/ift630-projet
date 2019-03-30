import argparse
import signal
import logging
import os
import time

from CameraThread import CameraThread


class App:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.logger = logging.getLogger('main')
        self.prepare_logger()
        self.camera_thread = CameraThread(args.capture_duration)

    def prepare_logger(self):
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())
        os.makedirs('log', exist_ok=True)
        self.logger.addHandler(logging.FileHandler('log/shadowCar.log'))

    def run(self):
        self.camera_thread.start()
        while self.camera_thread.continue_running:
            # This is needed since thread.join() blocks signals...
            time.sleep(1)
        self.camera_thread.join()

    def trigger(self, signum, frame):
        self.logger.info("Triggered")
        self.camera_thread.continue_running = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-duration', '-d', help='Max capture duration (in seconds)', default='300', type=int)
    args = parser.parse_args()
    app = App(args)
    signal.signal(signal.SIGINT, app.trigger)
    app.run()

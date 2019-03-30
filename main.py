import argparse
import signal
import logging
import os
import time

from CameraRecorder import CameraRecorder
from MicrophoneRecorder import MicrophoneRecorder


class App:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.logger = logging.getLogger('main')
        self.prepare_logger()
        self.camera_thread = CameraRecorder(args.capture_duration)
        self.microphone_thread = MicrophoneRecorder(args.capture_duration)

    def prepare_logger(self):
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        os.makedirs('log', exist_ok=True)
        self.logger.addHandler(logging.FileHandler('log/shadowCar.log'))

    def run(self):
        self.camera_thread.start()
        self.microphone_thread.start()
        while self.camera_thread.continue_running:
            # This is needed since thread.join() blocks signals... 🙄
            time.sleep(1)
        self.camera_thread.join()
        self.microphone_thread.join()
        self.logger.info("Application exited cleanly")
        exit(0)

    def trigger(self, signum, frame):
        self.logger.info("Triggered")
        self.camera_thread.continue_running = False
        self.microphone_thread.continue_running = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-duration', '-d', help='Max capture duration (in seconds)', default='300', type=int)
    args = parser.parse_args()
    app = App(args)
    signal.signal(signal.SIGINT, app.trigger)
    app.run()

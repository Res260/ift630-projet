import argparse
import logging
import os
import signal
import time
from queue import Queue

from Constants import Constants
from Recorder.CameraRecorder import CameraRecorder
from Recorder.MicrophoneRecorder import MicrophoneRecorder
from SaveManager import SaveManager
from Trigger.KeyboardTrigger import KeyboardTrigger


class App:
    def __init__(self, args: argparse.Namespace):
        self.logger = logging.getLogger('main')
        self.prepare_logger()

        self.args = args

        self.camera_data = Queue(maxsize=1)
        self.audio_data = Queue(maxsize=1)
        self.camera_thread = CameraRecorder(args.capture_duration, self.camera_data)
        self.microphone_thread = MicrophoneRecorder(args.capture_duration, self.audio_data)
        self.trigger_thread = KeyboardTrigger(self.trigger)
        self.save_trigger = Queue(maxsize=1)
        self.save_thread = SaveManager(self.save_trigger, self.camera_data, self.audio_data)
        self.continue_running = True

    def prepare_logger(self):
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        os.makedirs('log', exist_ok=True)
        self.logger.addHandler(logging.FileHandler('log/shadowCar.log'))

    def run(self):
        os.makedirs(Constants.TEMP_FOLDER, exist_ok=True)
        os.makedirs(Constants .SAVE_FOLDER, exist_ok=True)

        self.save_thread.start()
        self.trigger_thread.start()

        while self.continue_running:
            self.camera_thread.start()
            self.microphone_thread.start()
            while not self.camera_thread.ready or not self.microphone_thread.ready:
                pass  # Waiting actively :(
            self.camera_thread.can_start = True
            self.microphone_thread.can_start = True

            while self.camera_thread.continue_running:
                # This is needed since thread.join() blocks signals... 🙄
                time.sleep(1)
            self.camera_thread.join()
            self.microphone_thread.join()

            # Recreate threads so they can be restarted again...
            self.camera_thread = CameraRecorder(args.capture_duration, self.camera_data)
            self.microphone_thread = MicrophoneRecorder(args.capture_duration, self.audio_data )

        self.logger.info("Application exited cleanly")
        exit(0)

    def trigger(self):
        self.logger.info("Triggered")
        self.save_trigger.put(True)
        self.camera_thread.continue_running = False
        self.microphone_thread.continue_running = False

    def quit(self, signum, frame):
        self.continue_running = False
        self.trigger()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-duration', '-d', help='Max capture duration (in seconds)', default='300', type=int)
    args = parser.parse_args()
    app = App(args)
    signal.signal(signal.SIGINT, app.quit)
    app.run()

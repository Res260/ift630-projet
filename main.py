import argparse
import logging
import logging.handlers
import os
import signal
import time
from queue import Queue

from Constants import Constants
from Recorder.CameraRecorder import CameraRecorder
from Recorder.CarRecorder import CarRecorder
from Recorder.MicrophoneRecorder import MicrophoneRecorder
from SaveManager import SaveManager
from Trigger.MouseClickTrigger import MouseClickTrigger


class App:
    def __init__(self, args: argparse.Namespace):
        self.logger = logging.getLogger('main')
        self.prepare_logger()

        self.args = args

        self.camera_data = Queue(maxsize=1)
        self.audio_data = Queue(maxsize=1)
        self.car_data = Queue(maxsize=1)
        self.camera_thread = CameraRecorder(args.capture_duration, self.camera_data)
        self.microphone_thread = MicrophoneRecorder(args.capture_duration, self.audio_data)
        self.car_thread = CarRecorder(args.capture_duration, self.car_data)
        self.trigger_thread = MouseClickTrigger(self.trigger)
        self.save_trigger = Queue(maxsize=1)
        self.save_thread = SaveManager(self.save_trigger, self.camera_data, self.audio_data, self.car_data)
        self.continue_running = True

    def prepare_logger(self):
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        os.makedirs('log', exist_ok=True)
        self.logger.addHandler(logging.FileHandler('log/shadowCar.log'))

        data_logger = logging.getLogger('car.data')
        file_handler = logging.FileHandler(f'log/car_data_{time.time()}.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        data_logger.setLevel(logging.INFO)
        data_logger.addHandler(file_handler)

    def run(self):
        os.makedirs(Constants.TEMP_FOLDER, exist_ok=True)
        os.makedirs(Constants .SAVE_FOLDER, exist_ok=True)

        self.save_thread.start()
        self.trigger_thread.start()

        while self.continue_running:
            self.car_thread.start()
            self.camera_thread.start()
            self.microphone_thread.start()
            while not self.camera_thread.ready or not self.microphone_thread.ready or not self.car_thread.ready:
                pass  # Waiting actively :(
            self.camera_thread.can_start = True
            self.microphone_thread.can_start = True
            self.car_thread.can_start = True

            while self.camera_thread.continue_running:
                # This is needed since thread.join() blocks signals... 🙄
                time.sleep(1)
            self.camera_thread.join()
            self.microphone_thread.join()
            self.car_thread.join()

            # Recreate threads so they can be restarted again...
            self.camera_thread = CameraRecorder(args.capture_duration, self.camera_data)
            self.microphone_thread = MicrophoneRecorder(args.capture_duration, self.audio_data )
            self.car_thread = CarRecorder(args.capture_duration, self.car_data)

        self.logger.info("Application exited cleanly")
        exit(0)

    def trigger(self):
        self.logger.info("Triggered")
        self.save_trigger.put(True)
        self.camera_thread.continue_running = False
        self.microphone_thread.continue_running = False
        self.car_thread.continue_running = False

    def quit(self, signum, frame):
        self.continue_running = False
        self.trigger()
        exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-duration', '-d', help='Max capture duration (in seconds)', default='300', type=int)
    args = parser.parse_args()
    app = App(args)
    signal.signal(signal.SIGINT, app.quit)
    app.run()

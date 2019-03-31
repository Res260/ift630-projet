import argparse
import signal
import logging
import os
import subprocess
import threading
import time

from Recorder.CameraRecorder import CameraRecorder
from Constants import Constants
from Recorder.MicrophoneRecorder import MicrophoneRecorder


class App:
    def __init__(self, args: argparse.Namespace):
        self.SAVE_FOLDER = 'out/'
        self.TEMP_FOLDER = 'temp/'
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

        os.makedirs(self.TEMP_FOLDER, exist_ok=True)
        os.makedirs(self.SAVE_FOLDER, exist_ok=True)

        threading.Timer(5.0, lambda : self.trigger(None, None)).start()

        self.camera_thread.start()
        self.microphone_thread.start()
        while(not self.camera_thread.ready or not self.microphone_thread.ready):
            pass  # Waiting actively :(
        self.camera_thread.can_start = True
        self.microphone_thread.can_start = True

        while self.camera_thread.continue_running:
            # This is needed since thread.join() blocks signals... 🙄
            time.sleep(1)
        self.camera_thread.join()
        self.microphone_thread.join()
        self.merge_audio_and_video()
        self.logger.info("Application exited cleanly")
        exit(0)

    def trigger(self, signum, frame):
        self.logger.info("Triggered")
        self.camera_thread.continue_running = False
        self.microphone_thread.continue_running = False

    def merge_audio_and_video(self):
        self.logger.debug("Mixing audio and video")
        subprocess.run('ffmpeg -y -v 0 -i {0} -i {1} -c:v copy '
               '-c:a aac -strict experimental {2}'
               .format(Constants.TEMP_FOLDER + Constants.VIDEO_FILE,
                       Constants.TEMP_FOLDER + Constants.AUDIO_FILE,
                       Constants.SAVE_FOLDER + f"recording_{time.time()}.avi"))
        self.logger.debug("Mixing audio and video DONE")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture-duration', '-d', help='Max capture duration (in seconds)', default='300', type=int)
    args = parser.parse_args()
    app = App(args)
    signal.signal(signal.SIGINT, app.trigger)
    app.run()

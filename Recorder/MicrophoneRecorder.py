import logging
import threading
import time
from queue import Queue

import pyaudio as pa

from Constants import Constants
from Recorder.Recorder import Recorder


class MicrophoneRecorder(Recorder, threading.Thread):
    """
    Thread that fetches default microphone's content.
    """

    def __init__(self, capture_duration: int, audio_data: Queue):
        threading.Thread.__init__(self)
        Recorder.__init__(self, capture_duration)
        self.audio_data = audio_data
        self.logger = logging.getLogger('main.microphone')
        self.pyaudio = pa.PyAudio()

    def run(self):
        self.logger.debug("Starting microphone thread.")
        try:
            stream = self.pyaudio.open(format=Constants.FORMAT, channels=Constants.CHANNELS,
                            rate=Constants.SAMPLE_RATE, input=True,
                            frames_per_buffer=Constants.CHUNK_SIZE)
        except OSError as e:
            self.logger.error(f"Error when opening audio stream: {e}")
            self.logger.debug("Microphone thread stopped before starting")
            exit(1)
        self.logger.debug("Stream opened")

        self.ready = True
        self.wait_to_start()

        while self.continue_running:
            samples = stream.read(Constants.CHUNK_SIZE)
            current_time = time.time()
            self.remove_old_frames(current_time)
            self.queue.append((current_time, samples))
            # self.logger.info(len(self.queue))

        if stream is not None:
            stream.stop_stream()
            stream.close()

        self.audio_data.put(self.queue.copy())

        self.pyaudio.terminate()
        self.logger.debug("Microphone thread stopped")

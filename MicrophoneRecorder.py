import logging
import threading
import time

import pyaudio as pa

from Recorder import Recorder


class MicrophoneRecorder(Recorder, threading.Thread):
    """
    Thread that fetches default microphone's content.
    """

    def __init__(self, capture_duration: int):
        threading.Thread.__init__(self)
        Recorder.__init__(self, capture_duration)
        self.logger = logging.getLogger('main.microphone')
        self.CHUNK_SIZE = 2048
        self.FORMAT = pa.paInt32
        self.SAMPLE_RATE = 44100
        self.CHANNELS = 1

    def run(self):
        self.logger.debug("Starting microphone thread.")
        p = pa.PyAudio()
        stream = p.open(format=self.FORMAT, channels=self.CHANNELS,
                        rate=self.SAMPLE_RATE, input=True,
                        frames_per_buffer=self.CHUNK_SIZE)
        self.logger.debug("Stream opened")

        while self.continue_running:
            samples = stream.read(self.CHUNK_SIZE)
            current_time = time.time()
            self.remove_old_frames(current_time)
            self.queue.append((current_time, samples))
            self.logger.info(len(self.queue))

        self.logger.debug("Microphone thread stopped")


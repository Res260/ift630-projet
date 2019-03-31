import logging
import threading
import time
import wave

import pyaudio as pa

from Recorder.Recorder import Recorder
from Constants import Constants


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
        self.pyaudio = pa.PyAudio()

    def run(self):
        self.logger.debug("Starting microphone thread.")
        stream = self.pyaudio.open(format=self.FORMAT, channels=self.CHANNELS,
                        rate=self.SAMPLE_RATE, input=True,
                        frames_per_buffer=self.CHUNK_SIZE)
        self.logger.debug("Stream opened")

        self.ready = True
        self.wait_to_start()

        while self.continue_running:
            samples = stream.read(self.CHUNK_SIZE)
            current_time = time.time()
            self.remove_old_frames(current_time)
            self.queue.append((current_time, samples))
            self.logger.info(len(self.queue))

        stream.stop_stream()
        stream.close()

        self.write_to_disk()

        self.pyaudio.terminate()
        self.logger.debug("Microphone thread stopped")

    def write_to_disk(self):
        self.logger.debug("Saving microphone data to disk")
        frames = self.queue.copy()
        self.queue.clear()
        wf = wave.open(f'{Constants.TEMP_FOLDER}{Constants.AUDIO_FILE}', 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.pyaudio.get_sample_size(self.FORMAT))
        wf.setframerate(self.SAMPLE_RATE)
        for timestamp, frame in frames:
            wf.writeframes(frame)
        wf.close()

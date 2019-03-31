import pyaudio


class Constants:
    TEMP_FOLDER = 'temp/'
    SAVE_FOLDER = 'out/'
    VIDEO_FILE = 'camera_recorder.avi'
    AUDIO_FILE = 'microphone_recorder.wav'
    CHUNK_SIZE = 2048
    FORMAT = pyaudio.paInt16
    SAMPLE_RATE = 44100
    CHANNELS = 1

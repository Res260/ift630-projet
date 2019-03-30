from collections import deque


class Recorder:

    def __init__(self, capture_duration: int):
        self.capture_duration = capture_duration
        self.queue = deque()
        self.continue_running = True

    def remove_old_frames(self, current_time):
        if len(self.queue) > 0:
            continue_popping = True
            while continue_popping:
                if current_time - self.queue[0][0] > self.capture_duration:
                    # remove last frames
                    self.queue.popleft()
                else:
                    continue_popping = False

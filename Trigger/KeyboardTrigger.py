import logging
import threading
from pynput.keyboard import Key, Listener
from Trigger.Trigger import Trigger


class KeyboardTrigger(Trigger, threading.Thread):
    """
    Trigger class that triggers an action when a key is pressed on the keyboard.
    """
    def __init__(self, callback: callable):
        Trigger.__init__(self)
        threading.Thread.__init__(self)
        self.callback = callback
        self.logger = logging.getLogger('main.keyboardTrigger')

    def run(self):
        self.logger.debug("KeyboardTrigger started")
        with Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            listener.join()

    def on_press(self, key):
        self.logger.info('{0} pressed, triggering save event'.format(key))
        self.callback(None, None)

    def on_release(self, key):
        pass
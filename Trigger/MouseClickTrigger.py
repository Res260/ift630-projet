import io
import logging
import threading

try:
    import mouse
except io.UnsupportedOperation as e:
    logging.getLogger('main.mouseClickTrigger').error(f"Error: {e}")
    logging.getLogger('main.mouseClickTrigger').error(f"Make sure the mouse is plugged.")
    exit(1)

from Trigger.Trigger import Trigger


class MouseClickTrigger(Trigger, threading.Thread):
    """
    Trigger class that triggers an action when a mouse click is registered.
    """
    def __init__(self, callback: callable):
        Trigger.__init__(self)
        threading.Thread.__init__(self)
        self.callback = callback
        self.logger = logging.getLogger('main.mouseClickTrigger')

    def run(self):
        self.logger.debug("MouseClickTrigger started")
        mouse.on_click(self.on_click)

    def on_click(self):
        self.logger.debug("Mouse clicked")
        self.callback()

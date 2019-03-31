import logging
import threading
import time
from queue import Queue

import obd

from Recorder.Recorder import Recorder


class CarRecorder(Recorder, threading.Thread):
    """
    Thread that fetches the car's data using the OBD connection.
    """

    def __init__(self, capture_duration: int, car_data: Queue):
        threading.Thread.__init__(self)
        Recorder.__init__(self, capture_duration)
        self.car_data = car_data
        self.logger = logging.getLogger('main.car')
        self.data_logger = logging.getLogger('car.data')

    def run(self):
        """
        List of commands: https://python-obd.readthedocs.io/en/latest/Command%20Tables/
        """
        self.logger.debug("Starting car thread.")
        # obd.logger.setLevel(obd.logging.DEBUG)  # enables all debug information
        try:
            connection = obd.OBD(portstr='\\.\\COM4',
                                 baudrate=None,
                                 protocol="6",
                                 fast=True, timeout=0.1)
            self.logger.debug("Car ready")
            self.ready = True
            self.wait_to_start()
            if not connection.is_connected():
                self.logger.error("Can't connect to car.")
                self.continue_running = False
        except Exception as e:
            self.logger.error(f'Error when connecting to car: {e}')
            self.continue_running = False
            self.ready = True
            self.wait_to_start()

        while self. continue_running:
            current_time = time.time()
            self.remove_old_frames(current_time)

            data = {}
            self.query(connection, obd.commands.RPM, data, 'rpm')
            self.query(connection, obd.commands.SPEED, data, 'kmh')
            self.query(connection, obd.commands.RUN_TIME, data, 'runtime')
            self.query(connection, obd.commands.FUEL_LEVEL, data, 'fuel_level')
            self.query(connection, obd.commands.THROTTLE_POS, data, 'accelerator_pos')
            self.query(connection, obd.commands.DISTANCE_W_MIL, data, 'check_engine_on')
            self.query(connection, obd.commands.BAROMETRIC_PRESSURE, data, 'pressure')
            self.data_logger.info(data)
            self.queue.append((current_time, data))
            time.sleep(0.2)

        self.car_data.put(self.queue.copy())
        self.logger.debug("Car thread stopped")

    def query(self, connection, cmd, data, name):
        response = connection.query(cmd)
        data[name] = response.value.magnitude
        self.logger.debug(response)

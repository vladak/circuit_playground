"""
generic binary state tracking class

modified from the vladak/workmon/binarystate.py to track the time in miliseconds
"""

import time

import adafruit_logging as logging


class BinaryState:
    """
    provides state tracking based on updating value periodically
    The state duration is stored as float in order to allow for sub-second updates.
    This in turn can lead to lose of precision over time.
    """

    def __init__(
        self,
    ):
        """
        set the initial state
        """
        self.prev_state = None
        self.state_duration = 0
        self.stamp = time.monotonic_ns()  # use _ns() to avoid losing precision

    def update(self, cur_state) -> float:
        """
        :param cur_state: current state
        :return: duration of the state in miliseconds
        """
        logger = logging.getLogger(__name__)

        # Record the duration.
        if self.prev_state is not None:
            if self.prev_state == cur_state:
                self.state_duration += (
                    time.monotonic_ns() - self.stamp
                ) // 1_000_000
                logger.debug(
                    f"state '{cur_state}' preserved (for {self.state_duration} msec)"
                )
            else:
                logger.debug(f"state changed {self.prev_state} -> {cur_state}")
                self.state_duration = 0

        self.prev_state = cur_state
        self.stamp = time.monotonic_ns()

        return self.state_duration

    def reset(self):
        """
        reset the state
        """
        self.prev_state = None
        self.state_duration = 0

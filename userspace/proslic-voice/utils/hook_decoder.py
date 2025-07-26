
import logging
import time

from enum import Enum, auto

from config import HookConfig
from statuses import HookStatus

class HookEvent(Enum):
    HOOKFLASH = auto()
    PULSE_DIGIT = auto()
    ONHOOK_TIMEOUT = auto()
    OFFHOOK_TIMEOUT = auto()

class HookPulseDetector:
    def __init__(self, config: HookConfig):
        self._logger = logging.getLogger("HookPulseDetector")
        self.config = config

        # self.on_event = on_event  # callback: fn(event_type, details)

        self._hook_state = None
        self._transition_time = None
        self._event_time = None

        self._pulse_count = 0
        self._awaiting_timeout = False

    def setup(self, status: HookStatus):
        self._hook_state = status
        self._transition_time = time.time()

    def on_state_changed(self, timestamp, new_state: HookStatus):
        self._event_time = timestamp

        # Calculate delta from last transition
        delta = round(timestamp - self._transition_time, 3) # ms precision

        # State transition occurred
        if new_state != self._hook_state:
            self._hook_state = new_state
            self._transition_time = timestamp
            self._awaiting_timeout = True

            self._logger.debug(f"Detected Hook status change status={new_state} delta={delta} (s)")

            if new_state == HookStatus.UNHOOKED:
                # Detect pulse digit
                if self.config.min_digit <= delta <= self.config.max_digit:
                    self._pulse_count += 1
                # Detect hook flash
                elif self.config.min_flash <= delta <= self.config.max_flash:
                    self._emit(HookEvent.HOOKFLASH)
                    self._reset()

    def check_timeout(self):
        """Should be called periodically (less often), or via a timer."""
        if not self._awaiting_timeout:
            return

        now = time.time()
        delta = now - self._transition_time

        # Passed inter digit delay, so number ended or HOOKED
        # Here we detect those events that are triggered after a timeout
        if delta >= self.config.min_inter_digit:
            # We have past the min_hook_timeout, it cannot be a digit            
            if delta > self.config.min_hook_timeout:
                if self._hook_state == HookStatus.HOOKED:
                    self._emit(HookEvent.ONHOOK_TIMEOUT)
                else:
                    self._emit(HookEvent.OFFHOOK_TIMEOUT)
                self._reset()
            elif self._pulse_count > 0:
                self._emit(HookEvent.PULSE_DIGIT, self._pulse_count)
                self._reset()

    def _emit(self, event:HookEvent, data=None):
        self._logger.info(f"Detected hook event={event.name} data={data}")
        # if self.on_event:
        #     self.on_event(event, data)

    def _reset(self):
        self._pulse_count = 0
        self._awaiting_timeout = False
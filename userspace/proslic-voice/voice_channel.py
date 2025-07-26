import threading
import logging
import time

from typing import List

from config import DeviceConfig, FXSConfig
from core.device import SiDevice
from exceptions import RingUnhookException
from devices.si3228 import SI3228x_REGs
from utils.ring_pattern import RingPattern
from utils.resources import ProSLIC_IRQ2
from statuses import Linefeed, HookStatus, InterrupFlags

class VoiceChannel:
    
    def __init__(self, channel_id: int, device: SiDevice, fxs_config: FXSConfig):
        self.logger = logging.getLogger("VoiceChannel")

        self.channel_id = channel_id
        self.device = device
        self._fxs_config = fxs_config

        # Ring Patterns
        self._ring_patters: List[RingPattern] = []

        # Ringer configuration
        self._ringer_thread = None
        self._ringer_stop_event = threading.Event()
        self._ringer_lock = threading.Lock()

    def __str__(self):
        return f"VoiceChannel(name={self.device.name} chan={self.channel_id})"

    def getChannelId(self):
        return self.channel_id
    
    def begin(self, dev_config: DeviceConfig, ):
        self.logger.debug(dev_config)
        self.logger.debug(self._fxs_config)

        self.device.configureDCFeed(self.channel_id)
        self.device.configureRinger(self.channel_id)
        self.device.configureZsynth(self.channel_id, self._fxs_config.impedance)

        self.device.configurePCM(self.channel_id, dev_config.audio_codec)
        self.device.setPCMTimeslot(self.channel_id, self._fxs_config.audio_slot)

        self.device.enablePCM(self.channel_id)
        self.setLineFeed(Linefeed.NOP)
        self.device.setLoopback(self.channel_id, self._fxs_config.loopback)

        # Configure Ring Patterns
        self._ring_patters.append(RingPattern(self._fxs_config.ring_pattern))

        # Things to do to begin channel
        self.logger.debug("Enable channel by putting in IDLE state")
        self.setLineFeed(Linefeed.IDLE)

        self.logger.debug("Clear all enable IRQs as D2 implementation")
        self.device.disableIRQ(self.channel_id)

        self.logger.debug("Enable only Linefeed change IRQs")
        # FIXME: HARDCODED flags, pass flags to method below
        # self.device.enableIRQ(self.channel_id)
        self.device.writeRegister(
            self.channel_id, SI3228x_REGs.IRQEN2.value,
            ProSLIC_IRQ2.IRQ_LOOP_STATUS.value
        )
        # This should reset the device IRQ flags
        self.device.getInterruptChannels()
    
    def close(self):
        # Things to do to clear channel status
        self.stopRing()
        self.setLineFeed(Linefeed.NOP)

    def startRing(self, cid = None, pattern_idx = 0):
        if self.getHookState() == HookStatus.UNHOOKED:
             raise RingUnhookException()
        
        with self._ringer_lock:
            if self._ringer_thread and self._ringer_thread.is_alive():
                self.logger.warning("Ringer is already running.")
                return

            # Fetch a ring pattern
            pattrn = self._ring_patters[pattern_idx]
            if not pattrn:
                raise RuntimeError(f"Unable to find registered ring pattern with index={pattern_idx}")
            self._ringer_active_pattern = iter(pattrn)            
            
            # Create the thread
            self._ringer_stop_event.clear()
            self._ringer_thread = threading.Thread(target=self._ringerRun, daemon=True)
            self._ringer_thread.start()
            self.logger.info("Ringer thread started.")
        pass

    def stopRing(self):
        """Stop the ringer thread."""
        with self._ringer_lock:
            if not self._ringer_thread or not self._ringer_thread.is_alive():
                self.logger.warning("Ringer is not running.")
                return

            self.logger.info("Stopping ringer thread...")
            self._ringer_stop_event.set()
            self._ringer_thread.join()

            self._ringer_thread = None
            self.logger.info("Ringer thread stopped.")
        pass

    def isRinging(self):
        with self._ringer_lock:
            return self._ringer_thread and self._ringer_thread.is_alive()

    def getHookState(self):
        if self.device.getHookState(self.channel_id):
            return HookStatus.HOOKED
        else:
            return HookStatus.UNHOOKED        

    def setLineFeed(self, state: Linefeed):
        self.device.setLineFeed(self.channel_id, state)

    def testRing(self, delay = 10):
        self.logger.info("Performing Ring Test")

        if self.getHookState() == HookStatus.HOOKED:
            self.logger.info("Performing Ring Test")
            self.startRing()
            time.sleep(delay)
            self.stopRing()
            return True
        else:
            self.logger.warning("Phone is unkooked, cant perform Ring Test")
            return False

    def handle_interrupt(self, flags, timestamp):
        if InterrupFlags.LOOP in flags:            
            if self.isRinging():
                self.stopRing()
                self.logger.info(f"Stop ringing channel={self.channel_id} hook status changed!")

            hook_status = self.getHookState()
            self._hook_detector.on_state_changed(timestamp, hook_status)

    def _ringerRun(self):
        self.logger.debug("Ringer loop started.")

        state = Linefeed.RINGING
        try:
            while not self._ringer_stop_event.is_set():
                try:
                    delay = next(self._ringer_active_pattern)

                    self.logger.debug(f"Ring status={state}")
                    self.setLineFeed(state)

                    # Invert the state
                    if state == Linefeed.RINGING:
                        state = Linefeed.RING_IDLE
                    else:
                        state = Linefeed.RINGING
                    
                    self.logger.debug(f"Delay: {delay:.2f}s")
                    if self._ringer_stop_event.wait(delay):
                        break
                except StopIteration:
                    print("Ring pattern finished.")
                    break
        finally:
            # Ensure the device is stopped no matter what
            self.setLineFeed(Linefeed.IDLE)
            self.logger.debug("Ringer loop exited cleanly.")
    
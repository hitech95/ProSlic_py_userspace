import time
import logging
import threading
import traceback

from typing import List

from config import Config
from core.device import SiDevice
from core.dummy import DummyDevice
from voice_channel import VoiceChannel
from devices.si3228 import Si3228x

class PhoneManager:

    def __init__(self, config: Config, devfile):
        self.logger = logging.getLogger("PhoneManager")

        # FIXME: remove by moving this into SiDevice
        self.devfile = devfile

        self._config = config
        self._devices: List[SiDevice] = []
        self._channels: List[VoiceChannel] = []

        # Ringer configuration
        self._irq_thread = threading.Thread(target=self._irqRun, daemon=True)
        self._irq_stop_event = threading.Event()
        self._irq_lock = threading.Lock()

    def begin(self, device_paths):
        fxs_index = 0
        device_index = 0
        try:
            for path in device_paths:
                self.logger.info(f"Initializing device at {path}")
                dev_config = self._config.getDeviceConfig(device_index)
                self.logger.debug(dev_config)

                #FIXME: open and use path
                dummy = DummyDevice(self.devfile)
                dummy.setup()

                chip_id = dummy.getChipInfo()
                self.logger.info(f"Found chip with id={hex(chip_id)}")

                if chip_id == 0xCB:
                    device = Si3228x(self.devfile, dev_config.gpio_irq)
                else:
                    raise RuntimeError(f"Unknown chip id={hex(chip_id)} at {path}")

                if not device.setup():
                    self.logger.fatal(f"Cannot initialize device={dev_config}")
                    raise RuntimeError(f"Cannot initialize device at {path}")
                self._devices.append(device)
                device_index += 1

                for channel in range(device.numChannels):
                    self.logger.info(f"Mapping device channel {channel} -> PhoneManager channel {fxs_index}")
                    try:
                        fxs_config = self._config.getFXSConfig(fxs_index)

                        vc = VoiceChannel(device, channel)
                        vc.begin(dev_config, fxs_config)

                        self._channels.append(vc)                    
                        fxs_index += 1
                        # FIXME: this is here to prevent Exception
                        # break
                    except IndexError as e:
                        self.logger.error(e)
                        self.logger.fatal(f"Cannot find configuration for fxs={fxs_index}")

            # Start IRQ thread
            with self._irq_lock:
                self._irq_stop_event.clear()
                self._irq_thread.start()
            
            return True
        except Exception as e:
            self.logger.fatal(f"Cannot initialize PhoneManager")
            self.logger.error(e)
            traceback.print_exc()
            self.close()
            return False

    def close(self):
        self.logger.info("Closing all channels and devices...")

        # Stop IRQ Thread
        with self._irq_lock:
            self._irq_stop_event.set()
            if self._irq_thread.is_alive():
                self._irq_thread.join()

        for vc in self._channels:
            vc.close()
        for dev in self._devices:
            dev.close()

    def getChannelCount(self):
        return len(self._channels)

    def getChannel(self, channel=0):
        if 0 <= channel < len(self._channels):
            return self._channels[channel]
        raise IndexError(f"Channel {channel} out of range (0-{self.getChannelCount() - 1})")

    def _irqRun(self):
        while not self._irq_stop_event.is_set():
            # Process IRQ chip by chip
            for device in self._devices:
                try:
                    if not device.hasPendingInterrupt():
                        break

                    # We should handle the Chip interrupt here!
                    flags, channel = device.handleIRQ()

                    if not flags:
                        continue

                    # We should notify the appropiate voice channel
                    self.logger.debug(f"Interrupt for device={device.name} channel={channel} with flags={flags}")

                    # FIXME: find a way to identify this
                    vc = self._channels[0]

                    if vc.isRinging():
                        vc.stopRing()

                except Exception as e:
                    self.logger.fatal(f"Error handling IRQ for device={device.name}")
                    self.logger.error(e)
                    traceback.print_exc()
        pass            


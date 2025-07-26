import time
import logging
import queue
import threading
import traceback

from typing import List, Dict, Tuple, Optional

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
        self._channel_map: Dict[Tuple[int, int], int] = {}

        # IRQ handler threading
        self._irq_queue = queue.Queue()
        self._irq_thread = threading.Thread(target=self._irq_run, daemon=True)
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
                dummy = DummyDevice(-1, self._irq_queue, self.devfile)
                dummy.setup()

                chip_id = dummy.getChipInfo()
                self.logger.info(f"Found chip with id={hex(chip_id)}")

                if chip_id == 0xCB:
                    device = Si3228x(device_index, self._irq_queue, dev_config, self.devfile)
                else:
                    raise RuntimeError(f"Unknown chip id={hex(chip_id)} at {path}")

                if not device.setup():
                    self.logger.fatal(f"Cannot initialize device={dev_config}")
                    raise RuntimeError(f"Cannot initialize device at {path}")
                self._devices.append(device)

                for channel in range(device.numChannels):
                    self.logger.info(f"Mapping device={device} channel={channel} -> PhoneManager channel={fxs_index}")
                    try:
                        fxs_config = self._config.getFXSConfig(fxs_index)

                        vc = VoiceChannel(channel, device, fxs_config)
                        vc.begin(dev_config)

                        self._channels.append(vc)
                        self._channel_map[(device_index, channel)] = fxs_index
                        #
                        fxs_index += 1
                    except IndexError as e:
                        self.logger.error(e)
                        self.logger.fatal(f"Cannot find configuration for fxs={fxs_index}")
                #
                device_index += 1

            # Start IRQ thread
            # FIXME: we should clear all the IRQs until now 
            # they were generated during init sequence
            # Not thread-safe!
            self._irq_queue.queue.clear()  
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

    def _device_lookup_by_id(self, index) -> Optional[SiDevice]:    
        return self._devices[index] if index < len(self._devices) else None

    def _channel_lookup_by_device_id(self, device_id, channel) -> Optional[VoiceChannel]:
        channel = self._channel_map.get((device_id, channel))
        if channel is not None:
            return self._channels[channel]
        return None

    def _irq_run(self):
        while not self._irq_stop_event.is_set():
            # Process IRQ queue
            try:
                # Timeout allow safe exit on close()
                irq_event = self._irq_queue.get(timeout=1.0)

                device_id = irq_event['device']
                payload = irq_event['data']
                timestamp = irq_event['timestamp']

                device = self._device_lookup_by_id(device_id)  # you'd define this
                if device is None:
                    self.logger.warning(f"No mapped device={device_id}")

                # Get wich channel triggered the IRQ, read IRQ flasg for the triggered channels
                for channel, pending_registers in device.getInterruptChannels(payload):
                    vc = self._channel_lookup_by_device_id(device_id, channel)
                    if vc is None:
                        self.logger.warning(f"No channel mapped for device={device} channel={channel}")
                        continue
                    
                    # Forward flags to the right VoiceChannel
                    flags = device.handleIRQ(channel, pending_registers)
                    vc.handle_interrupt(flags, timestamp)
            except queue.Empty:
                continue


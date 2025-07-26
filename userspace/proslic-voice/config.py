import os
import logging
import traceback

from dataclasses import dataclass
from enum import Enum

from uci import Uci, UciException, UciExceptionNotFound # pyuci

from statuses import LineTermination, LoopbackMode, AudioPCMFormat

class IRQMode(Enum):
    NONE = 'none'
    GPIO = 'gpio'
    DEVICE = 'device'

@dataclass
class HookConfig:
    min_hook_timeout: float
    min_digit: float
    max_digit: float
    min_flash: float
    max_flash: float
    min_inter_digit: float

@dataclass
class DeviceConfig:
    path: str
    irq: IRQMode
    audio_codec: AudioPCMFormat
    audio_device: str
    # Optional
    irq_gpiochip: str = '/dev/gpiochip0'
    irq_gpio: int = -1

@dataclass
class FXSConfig:
    # name: str
    audio_slot: int
    impedance: LineTermination
    ring_pattern: str
    tone_busy: str
    tone_dial: str
    hook_config: HookConfig
    loopback: LoopbackMode = LoopbackMode.NONE  # Optional

# Mapping for Enums
_logger_map = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR
}
_irq_map = {
    "none": IRQMode.NONE,
    "gpio": IRQMode.GPIO,
    "device": IRQMode.DEVICE,
}
_codec_map = {
    "pcm": AudioPCMFormat.FMT_PCM,
    "alaw": AudioPCMFormat.FMT_UNKOWN_A,
    "ulaw": AudioPCMFormat.FMT_UNKNOWN_B
}
_impedance_map = {
    "FCC": LineTermination.FCC,
    "TBR21": LineTermination.TBR21,
    "BT3": LineTermination.BT3,
    "TN12": LineTermination.TN12
}
_loopback_map = {
    "none": LoopbackMode.NONE,
    "loopback_a": LoopbackMode.LOOPBACK_A,
    "loopback_b": LoopbackMode.LOOPBACK_B
}

class Config:
    def __init__(self, config_file="voip"):
        self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)

        self.config_file = config_file
        self.uc = Uci()        

    def begin(self):
        """Initialize config and returns set of device paths"""
        try:
            self.logger.info("Loading configuration")
            self.uc.get(self.config_file)

            level = self.getLogLevel()
            logging.basicConfig(level=level)

            device_paths = set()
            device_sections = self._findSections("device")

            for section in device_sections:
                device_paths.add(self.uc.get(self.config_file, section, "path"))

            return device_paths
        except UciExceptionNotFound as e:
            self.logger.warning(f"Config '{self.config_file}' not found. Creating defaults...")
            self._create_default_config()            
            return False

    def getLogLevel(self):
        """Return log level"""
        try:
            glb = self._findSection("global")
            level_str = self.uc.get(self.config_file, glb, "log_level").lower()
            level = _logger_map.get(level_str)
            if not level:
                raise ValueError(f"Unknown log_level: {level_str}")
        except UciExceptionNotFound as e:
            self.logger.error(e)
            # Write missing configuration
            self.uc.set(self.config_file, glb, "log_level", 'info')
            self.uc.commit()
            level = logging.INFO
            pass

        return level

    def getGlobalConfig(self):
        """Return global device config dict"""
        name = self.findSection("global")

        if name:
            return self.uc.get_all(self.config_file, "cfg013fd6")
        return None
    
    def getDeviceConfig(self, index):
        """Return dict of DEVICE configuration"""
        device_sections = self._findSections('device')
        if index >= len(device_sections):
            raise IndexError(f"No DEVICE configuration for index {index}")
    
        dev_cfg = self.uc.get_all(self.config_file, device_sections[index])

        irq = _irq_map.get(dev_cfg.get("irq", 'none').lower())

        audio_codec = _codec_map.get(dev_cfg.get("audio_codec").lower())
        if not audio_codec:
            raise ValueError(f"Unknown audio_codec: {dev_cfg['audio_codec']}")

        return DeviceConfig(
            path=dev_cfg["path"],
            irq=irq,
            audio_codec=audio_codec,
            audio_device=dev_cfg["audio_device"],
            irq_gpiochip=dev_cfg.get("irq_gpiochip", ''),
            irq_gpio=int(dev_cfg.get("irq_gpio", -1)),
        )

    def getFXSConfig(self, index):
        """Return dict of FXS channel configuration"""
        fxs_sections = self._findSections('fxs')
        if index >= len(fxs_sections):
            raise IndexError(f"No FXS configuration for index {index}")
        
        fxs_cfg = self.uc.get_all(self.config_file, fxs_sections[index])        
    
        impedance = _impedance_map.get(fxs_cfg.get('impedance', '').upper())
        if not impedance:
            raise ValueError(f"Unknown impedance: {fxs_cfg.get('impedance')}")

        loopback = _loopback_map.get(
            fxs_cfg.get("loopback", "none").lower(),
              LoopbackMode.NONE
        )

        # Optional hook config
        hook_config = HookConfig(
            min_hook_timeout = float(fxs_cfg.get("min_hook_timeout", 0.850)),
            min_digit        = float(fxs_cfg.get("min_digit", 0.020)),
            max_digit        = float(fxs_cfg.get("max_digit", 0.080)),
            min_flash        = float(fxs_cfg.get("min_flash", 0.100)),
            max_flash        = float(fxs_cfg.get("max_flash", 0.800)),
            min_inter_digit  = float(fxs_cfg.get("min_inter_digit", 0.090)),
        )

        return FXSConfig(
            # name=fxs_cfg["name"],
            audio_slot=int(fxs_cfg.get("audio_slot", 0)),
            impedance=impedance,
            ring_pattern=fxs_cfg.get("ring_pattern"),
            tone_busy=fxs_cfg.get("tone_busy"),
            tone_dial=fxs_cfg.get("tone_dial"),
            hook_config=hook_config,
            loopback=loopback,
        )

    def _create_default_config(self):
        """Creates a default UCI configuration"""

        self.logger.debug("_create_default_config()")
        try:
            path = self.uc.confdir()

            # Crete empty file
            with open(os.path.join(path, self.config_file), 'w') as fp:
                pass

            # Create the nodes
            glb = self.uc.add(self.config_file, "global")
            dev = self.uc.add(self.config_file, "device")
            fxs = self.uc.add(self.config_file, "fxs")

            # Write global configuration
            self.uc.set(self.config_file, glb, "log_level", "debug")

            # Add one device configuration
            self.uc.set(self.config_file, dev, "proslic")
            self.uc.set(self.config_file, dev, "path", "/dev/proslic")
            self.uc.set(self.config_file, dev, "irq", "device")
            self.uc.set(self.config_file, dev, "audio_codec", "pcm")
            self.uc.set(self.config_file, dev, "audio_device", "hw:0,0")

            # Add one default FXS channel
            self.uc.set(self.config_file, fxs, "Phone1")
            self.uc.set(self.config_file, fxs, "audio_slot", "0")
            self.uc.set(self.config_file, fxs, "impedance", "TBR21")
            self.uc.set(self.config_file, fxs, "ring_pattern", "60(2/4)")
            self.uc.set(self.config_file, fxs, "tone_busy", "425@-5;20(.5/.5/1)")
            self.uc.set(self.config_file, fxs, "tone_dial", "425@-5;10(.2/.2/1,.6/1/1)")

            self.uc.commit(self.config_file)

        except UciException as e:
            self.uc.revert(self.config_file)
            self.logger.critical(e)
            traceback.print_exc()
    
    def _findSection(self, type):
        configs = self.uc.get_all(self.config_file)

        for section_key, section_data in configs.items():
            if self.uc.get(self.config_file, section_key) == type:
                return section_key

        return None
    
    def _findSections(self, type):
        configs = self.uc.get_all(self.config_file)
        keys = []
        for section_key, section_data in configs.items():
            if self.uc.get(self.config_file, section_key) == type:
                keys.append(section_key)

        return keys

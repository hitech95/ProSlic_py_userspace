from utils.gpio_manager import GPIOManager
from ..utils.spi_device import SPIDevice
from ..utils.gpio_manager import GPIOManager

from .resources import ProSLIC_OpCodes, ProSLIC_CommonREGs, PROSLIC_RETRIES, CHANNEL_IDs, PROSLIC_PROTO_OP_BYTE, PROSLIC_PROTO_REG_BYTE


class SiVoice():
    def __init__(self):
        # FIXME - This must be calculated at runtime!
        self.numChannels = 0

from ..device import SiDevice


class Si32282(SiDevice):
    def __init__(self, spiBus, spiDevice, spiMode, spiSpeed=100000):
        super().__init__(spiBus, spiDevice, spiMode, spiSpeed)

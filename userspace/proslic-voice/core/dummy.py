from core.device import SiDevice

from statuses import LineTermination, AudioPCMFormat
from exceptions import DeviceError, InitializationError

class DummyDeviceError(DeviceError):
    def __init__(self, device):
        super().__init__(device, "Dummy device, not available")

class DummyDevice(SiDevice):
    NAME = "PROSLIC_DUMMY"

    def __init__(self, device):
        super().__init__(self.NAME, device)

    def setup(self):
        try:
            # HW Reset
            self.reset()

            return True
        except Exception as e:
            self.logger.error("Exception while initializing.")
            self.logger.error(e)
            raise InitializationError(self)
    
    def configure(self, channel = 0):
        raise DummyDeviceError(self)

    def enableDCDCRegulator(self, channel = 0):
        raise DummyDeviceError(self)

    def configureDCFeed(self, channel):
        raise DummyDeviceError(self)

    def configureRinger(self, channel):
        raise DummyDeviceError(self)

    def configureZsynth(self, channel, lineType: LineTermination):
        raise DummyDeviceError(self)

    def configurePCM(self, channel, format: AudioPCMFormat):
        raise DummyDeviceError(self)
    
    def enableIRQ(self, channel = 0):
       raise DummyDeviceError(self)
    
    def disableIRQ(self, channel = 0):
       raise DummyDeviceError(self)

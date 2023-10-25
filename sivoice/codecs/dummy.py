from cgi import test
from sivoice.resources import CHANNEL_IDs, ProSLIC_CommonREGs
from ..device import SiDevice
from utils.gpio_manager import GPIOManager
from utils.spi_device import SPIDevice


class SiDummy(SiDevice):
    NAME = "SIVOICE_DUMMY"

    def __init__(self, reset_pin, spiBus, spiDevice, spiMode, spiSpeed=10000, irq_pin=-1):
        super().__init__(self.NAME, reset_pin, spiBus,
                         spiDevice, spiMode, spiSpeed, irq_pin)

        # This is used to calculate the nummber of channels at RUN time
        self.numChannels = len(CHANNEL_IDs)

    def close(self):
        self.gpioManager.close()
        print("Dummy.close")

    def getChannelCount(self):
        chanCount = len(CHANNEL_IDs)
        print(f"We can scan up to {chanCount} channels")

        count = 0
        for i in range(chanCount):
            print(f"Scanning chan {hex(CHANNEL_IDs[i])}")
            id = self.getChipInfo(i)
            if (id != 0xFF):
                count += 1
                print(f"Found device with ID: {hex(id)} on chan: {i}")
        return count

    def testSPI(self, channel):
        self.writeRegister(channel, ProSLIC_CommonREGs.MSTRSTAT.value, 0xFF)
        data = self.readRegister(channel,  ProSLIC_CommonREGs.MSTRSTAT.value)
        if data == 0x1F:
            return True
        return False

    def testRAM(self, channel, testData=0x12345678):
        self.writeRam(channel, 0x1c1, testData)
        readData = self.readRam(channel, 0x1c1)
        if readData == testData:
            return True
        return False

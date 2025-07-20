from time import sleep

from utils.spi_device import SPIDevice
from utils.gpio_manager import GPIOManager

from .resources import ProSLIC_CommonRamAddrs, ProSLIC_OpCodes, ProSLIC_CommonREGs, PROSLIC_RETRIES, CHANNEL_IDs, PROSLIC_PROTO_OP_BYTE, PROSLIC_PROTO_REG_BYTE


class SiDevice(SPIDevice):
    def __init__(self, name, reset_pin, spiBus, spiDevice, spiMode, spiSpeed=100000, irq_pin=-1):
        # Call constructor of SPIDevice
        super().__init__(spiBus, spiDevice, spiMode, spiSpeed)

        # Call constructor of GPIOManager
        self.gpioManager = GPIOManager(name, reset_pin, irq_pin)
        print(self.gpioManager)

        # FIXME - This must be calculated at runtime!
        self.numChannels = 0

    def setup(self):
        try:
            self._open()

            self.gpioManager._setup()
            self.gpioManager.setReset(False)
            self.delay(200)

            # Disable reset
            # print(self.gpioManager)
            self.gpioManager.setReset(True)
            self.delay(400)

            return 0
        except Exception as e:
            print("Exception while opening")
            print(e)
            return -1

    def writeRegister(self, channel, reg, data):
        data_stream = bytearray(4)

        if channel == ProSLIC_OpCodes.BCAST.value:
            data_stream[PROSLIC_PROTO_OP_BYTE] = ProSLIC_OpCodes.BCAST.value | ProSLIC_OpCodes.CHANNEL_WR.value
        elif channel >= self.numChannels:
            return -1
        else:
            data_stream[PROSLIC_PROTO_OP_BYTE] = ProSLIC_OpCodes.CHANNEL_WR.value | CHANNEL_IDs[channel]

        data_stream[PROSLIC_PROTO_REG_BYTE] = reg
        data_stream[2] = data_stream[3] = data

        self.write(data_stream)
        return 0

    def readRegister(self, channel, reg):
        data_stream = bytearray(4)

        if channel >= self.numChannels:
            return -1
        else:
            data_stream[PROSLIC_PROTO_OP_BYTE] = ProSLIC_OpCodes.CHANNEL_RD.value | CHANNEL_IDs[channel]

        data_stream[PROSLIC_PROTO_REG_BYTE] = reg

        # Set the register to a non-zero value
        data_stream[2] = 0xFF
        self.write(data_stream[:2])
        readData = self.read(2)

        return readData[0]

    def waitRam(self, channel):
        count = PROSLIC_RETRIES
        data = 0xFF

        while count > 0 and data:
            data = self.readRegister(
                channel, ProSLIC_CommonREGs.RAM_STAT.value) & 0x1

            if data:
                self.delay(5)
            count -= 1

        if count > 0:
            return False
        return True  # Timed out

    def writeRam(self, channel, address, data):
        # Wait for the RAM to be available or no operation is in progress
        if self.waitRam(channel):
            return -1

        # The data is 29bit so we have to split
        # into different registers to write it.
        #
        # The address seems to be 11/12bit so we have to split the
        # address in two. We don't know why we need to write the HI part
        # in the beginning and the LOW part at the end.
        # Probably they will internally signal an BEGIN and COMMIT operaion
        # The LOW part of the address is varing and we think that only the
        # top 4 bits are spllitted.
        #
        # The biggest Hi address observed is 0xC0.
        # We have observed that the lowest 5 bits are always 0

        # The HI part of the address is created by taking
        # the most 3/4 significant bits and by shifting them right by 3.
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_HI.value, (address >> 3) & 0xE0)

        # In the ram values set on data rgisters always have the last
        # 3-bits set to 0 so I'm assuming the data is shifted
        # to keep a sort of 32bit MSB alignement. This remembers
        # left justified PCM / I2S.
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_D0.value, (data << 3) & 0xFF)
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_D1.value, (data >> 5) & 0xFF)
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_D2.value, (data >> 13) & 0xFF)
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_D3.value, (data >> 21) & 0xFF)

        # Write/COMMIT OPs?
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_LO.value, address & 0xFF)

        # Write operation succeeded?
        return self.waitRam(channel)

    def readRam(self, channel, address):

        # Wait for the RAM to be available or no operation is in progress
        if self.waitRam(channel) != 0:
            return -1

        # HI RAM ADDR
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_HI.value, (address >> 3) & 0xE0)
        # LOW RAM ADDR
        self.writeRegister(
            channel, ProSLIC_CommonREGs.RAM_LO.value, address & 0xFF)

        # Wait for the RAM to be available or no operation is in progress
        if self.waitRam(channel) != 0:
            return -1

        # READ DATA Registers
        data = self.readRegister(
            channel, ProSLIC_CommonREGs.RAM_D3.value) << 21
        data = data | self.readRegister(
            channel, ProSLIC_CommonREGs.RAM_D2.value) << 13
        data = data | self.readRegister(
            channel, ProSLIC_CommonREGs.RAM_D1.value) << 5
        data = data | self.readRegister(
            channel, ProSLIC_CommonREGs.RAM_D0.value) >> 3

        return data

    # The blob loading sequence consist in:
    # - doing a sequence of operation on register 0x7e
    # - setting JMPEN to 0x00 disable blob/fw?
    # - doing other stuff on some JMPxxx registers
    # - writing 0x00 to a specific ram address 0x54e (Blob load address?)
    # - dumping the blob into a specific ram address 0x54f (Blob data address?)
    # - resetting RAM_ADDR_HI to 0x00 (Blob load confirm?)
    # - the JMPxxx register are reconfigured ? FW config of some sort?
    # - re-setting JMPEN to 0x00 disable blob/fw so JMPxxx might enable initialize the blob?
    # - Reading the blob data back (write verify of some sort, 0x0 is written
    #    to 0x54e then the data is read many times again from address 0x54f)
    # - resetting RAM_ADDR_HI to 0x00 (Blob load confirm?)
    # - reading JMPxxx to find match to previous writes
    # - writing 0x101 to JMPEN
    # The second channel dont have the full patch setup. No idea on wht is skipped.
    #  more analysis is needed!
    def loadBlob(self, blob):
        channel = 0
        print(f"Attempting to load blob with ID:{hex(blob.id)}")

        # Before blob data
        data = self.readRegister(channel, 0x7E)
        print(f"Read register 0x7E with value {hex(data)} ")

        # Assuming we have to pass value just read?
        self.writeRegister(channel, 0x7E, 0x02)
        self.writeRegister(channel, 0x7E, 0x08)
        self.writeRegister(channel, 0x7E, 0x0E)
        self.writeRegister(channel, 0x7E, 0x00)

        # Disable blob?
        self.writeRegister(channel, ProSLIC_CommonREGs.JMPEN.value, 0x00)
        print(f"Disabled JMP, no fw now?")

        # Unconfigure JMP stuff
        # We dont know the logic, so add a reset table in the blob
        self.configureJMPBlob(channel, [0] * 16, [0] * 8)
        print(f"rst JMP, no fw now?")

        # Send the actual blob of data
        self.loadBlobData(channel, blob.data)
        print(f"blob data loaded")

        # Reconfigure JMP stuff
        self.configureJMPBlob(channel, blob.regJMPTable, blob.ramJMPTable)
        print(f"blob JMP tables loaded")


        # IDK blob ID or something? Not shared between the chan0 or chan1
        # Not shared with previous JMP disable/unconfigure
        self.writeRam(channel, ProSLIC_CommonRamAddrs.BLOB_ID.value, blob.id)
        print(f"blob ID loaded")

        # Next step is shared between chan0 and chan1
        self.configureBlob(channel, blob.configuration)
        print(f"blob configuration")

        # Verify if the blob has all been sent correctly
        if not self.verifyBlobData(channel, blob.data):
            print("Blob write failed! How can we signal this?, invalidating ID?")
            return -1
        
        # TODO - More stuff to check later
        # verify JMP table
        # verify Blob configuration

        # Enable blob (finally)?
        self.writeRegister(channel, ProSLIC_CommonREGs.JMPEN.value, 0x01)
        print(f"blob enabled")

        pass

    def configureJMPBlob(self, channel, regJMPs, ramJMPs):
        # Iterate through the configuration and configure the registers
        for idx, value in enumerate(regJMPs):
            self.writeRegister(channel, ProSLIC_CommonREGs.JMP0LO.value + idx, value)

        # More unknown stuff but *seems* related to JMP regs
        # Iterate through the configuration and configure the registers
        for idx, value in enumerate(ramJMPs):
            self.writeRam(
                channel, ProSLIC_CommonRamAddrs.BLOB_JMP_TABLE2.value + idx, value)

    def configureBlob(self, channel, configuration):
        # Iterate through the configuration and configure the registers
        for reg, value in configuration.items():
            self.writeRam(channel, reg, value)

    def loadBlobData(self, channel, blobData):
        if len(blobData) == 0:
            # Throw some sort of exception here!?
            return False

        # We suppose this is a auto increment register
        # if we read it after each write it get auto-incremented.
        self.writeRam(
            channel, ProSLIC_CommonRamAddrs.BLOB_DATA_ADDR.value, 0x00)

        for data in blobData:
            self.writeRam(
                channel, ProSLIC_CommonRamAddrs.BLOB_DATA_DATA.value, data)

        # Signaling write completed
        self.writeRegister(channel, ProSLIC_CommonREGs.RAM_HI.value, 0x00)

    def verifyBlobData(self, channel,  blob):
        correct = True

        # No patch to verify return OK?
        if len(blob) == 0:
            return correct

        # Disable blob (before reading)?
        self.writeRegister(channel, ProSLIC_CommonREGs.JMPEN.value, 0x00)

        # FIXME - Hardcoded address?
        # RAM_LOAD_ADDDRESS
        self.writeRam(
            channel, ProSLIC_CommonRamAddrs.BLOB_DATA_ADDR.value, 0x00)

        for data in blob:
            # FIXME - Hardcoded address?
            # RAM_LOAD_DATA
            readData = self.readRam(
                channel, ProSLIC_CommonRamAddrs.BLOB_DATA_DATA.value)
            if readData != data:
                correct = False
                break

        # Signaling write completed
        self.writeRegister(channel, ProSLIC_CommonREGs.RAM_HI.value, 0x00)

        # Do we have to do something if the blob is wrong?
        if not correct:
            pass

        return correct

    def reset(self, channel):
        pass

    def getErrors(self, channel):
        pass

    def clearErrors(self, channel):
        pass

    def getChipInfo(self, channel):
        return self.readRegister(channel, ProSLIC_CommonREGs.ID.value)

    def init(self, channel):
        pass

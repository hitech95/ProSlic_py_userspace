import time
import logging
import fcntl
import struct
import threading
import queue

from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Tuple, List, Any

from utils.resources import CHANNEL_COUNT, PROSLIC_RETRIES, ProSLIC_CommonREGs, ProSLIC_CommonRamAddrs, ProSLIC_IRQ1, ProSLIC_IRQ2, ProSLIC_IRQ3
from exceptions import TimeoutError, InitializationError, BlobInvalidError, BlobUploadError, BlobVerifyError, InvalidCalibrationError
from statuses import Linefeed, InterrupFlags, LineTermination, LoopbackMode, AudioPCMFormat

# Matches struct proslic_access in driver
IOCTL_READ_REG = 0x80087001  # _IOR('p', 1, struct proslic_access)
IOCTL_WRITE_REG = 0x40087002
IOCTL_READ_RAM  = 0x80087003
IOCTL_WRITE_RAM = 0x40087004
#
IOCTL_RESET_DEVICE = 0x40087007

# struct proslic_access { __u8 channel; __u16 address; __u32 data; }
STRUCT_FMT = "BHI"

IRQResult = namedtuple("IRQResult", ["IRQ1", "IRQ2", "IRQ3", "IRQ4"])

class SiDevice(ABC):

    LOW_TO_HIGH_IRQ_MAP = {
        ProSLIC_IRQ1.IRQ_FSKBUF_AVAIL: None,  # if not used
        ProSLIC_IRQ2.IRQ_LOOP_STATUS: InterrupFlags.LOOP,
        ProSLIC_IRQ2.IRQ_DTMF: InterrupFlags.DTMF,
        # Add more here as needed
    }
    
    def __init__(self, device_id: Any, name: str, interupt_queue: queue.Queue , device):
        self.logger = logging.getLogger(name)

        self._device_id = device_id
        self.name = name
        self._interupt_queue = interupt_queue
        self.dev = device

        self.numChannels = 0

        self._lock = threading.Lock()

    def __str__(self):
        return f"SiDevice(name={self.name} id={self._device_id})"

    # FIXME: 2025 Ghidra: part specific function, global wrapper method exist
    def setup(self):
        try:
            # HW Reset
            self.reset()

            # Probe channel count
            self.numChannels = self.getChannelCount()
            self.logger.info(f"Found {self.numChannels} channels")

            return True
        except Exception as e:
            self.logger.error("Exception while initializing.")
            self.logger.error(e)
            raise InitializationError(self)

    def reset(self):
        with self._lock:
            buf = struct.pack(STRUCT_FMT, 0, 0, 0)
            fcntl.ioctl(self.dev, IOCTL_RESET_DEVICE, buf)
            self.logger.info("Reset")

    def readRegister(self, channel, reg):
        with self._lock:
            buf = struct.pack(STRUCT_FMT, channel, reg, 0)
            result = fcntl.ioctl(self.dev, IOCTL_READ_REG, buf)
            _, _, data = struct.unpack(STRUCT_FMT, result)
            return data & 0xFF

    def writeRegister(self, channel, reg, value):
        with self._lock:
            buf = struct.pack(STRUCT_FMT, channel, reg, value & 0xFF)
            fcntl.ioctl(self.dev, IOCTL_WRITE_REG, buf)

    def readRam(self, channel, addr):
        with self._lock:
            buf = struct.pack(STRUCT_FMT, channel, addr, 0)
            result = fcntl.ioctl(self.dev, IOCTL_READ_RAM, buf)
            _, _, data = struct.unpack(STRUCT_FMT, result)
            return data

    def writeRam(self, channel, addr, value):
        with self._lock:
            buf = struct.pack(STRUCT_FMT, channel, addr, value)
            fcntl.ioctl(self.dev, IOCTL_WRITE_RAM, buf)
    
    def getChipInfo(self, channel = 0):
        return self.readRegister(channel, ProSLIC_CommonREGs.ID.value)
    
    def identifyChannel(self, channel):
        self.writeRegister(channel, ProSLIC_CommonREGs.PCMTXHI.value, 0x13)
        self.delay(10)
        data = self.readRegister(channel, ProSLIC_CommonREGs.PCMTXHI.value)

        # We want only specific type of channels
        return data == 0x13
    
    def getChannelCount(self):
        self.logger.debug(f"We can scan up to {CHANNEL_COUNT} channels")

        count = 0
        for idx in range(CHANNEL_COUNT):
            # self.logger.debug(f"Scanning chan {idx}")
            # getChipInfo can contains additional logic, basic probe here
            id = self.readRegister(idx, ProSLIC_CommonREGs.ID.value)
            if (id == 0xFF):
                break

            # if not self.testRegisters(idx):
            #     break

            self.logger.debug(f"Found device with ID: {hex(id)} on chan: {idx}")
            count += 1
        return count
    
    def testRegisters(self, channel, testData=0x5a):
        self.writeRegister(channel, ProSLIC_CommonREGs.PCMTXLO.value, testData)
        readData = self.readRegister(channel, ProSLIC_CommonREGs.PCMTXLO.value)
        if readData == testData:
            return True
        return False
    
    def testRAM(self, channel, testData=0x12345678):
        self.writeRam(channel, ProSLIC_CommonRamAddrs.TEST_IO.value, testData)
        readData = self.readRam(channel, ProSLIC_CommonRamAddrs.TEST_IO.value)
        if readData == testData:
            return True
        return False

    def enterUserMode(self, channel = 0):
        readData = self.readRegister(channel, ProSLIC_CommonREGs.USERMODE.value)

        # First bit seems to define User-Mode
        # assumed seeing what has appened during blob load:
        if (readData & 0x01):
            return

        self.writeRegister(channel, ProSLIC_CommonREGs.USERMODE.value, 0x02)
        self.writeRegister(channel, ProSLIC_CommonREGs.USERMODE.value, 0x08)
        self.writeRegister(channel, ProSLIC_CommonREGs.USERMODE.value, 0x0E)
        self.writeRegister(channel, ProSLIC_CommonREGs.USERMODE.value, 0x00)

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
        self.logger.info(f"Attempting to load blob with ID:{hex(blob.id)}")

        for channel in range(self.numChannels):
            try:
                self.enterUserMode(channel)

                # Disable blob?
                self.writeRegister(channel, ProSLIC_CommonREGs.JMPEN.value, 0x00)
                self.logger.debug(f"Disabled JMP, no fw now?")

                if channel == 0:
                    # Clear JMP stuff
                    # We dont know the logic, so add a reset table in the blob
                    self.logger.debug(f"Clear JMP tables")
                    self.configureJMPBlob(channel, [0] * 16, [0] * 8)

                    # Send the actual blob of data
                    self.loadBlobData(channel, blob)

                    # Reconfigure JMP stuff
                    self.configureJMPBlob(channel, blob.regJMPTable, blob.ramJMPTable)

                    # IDK blob ID or Version? Not shared between the chan0 or chan1
                    # Not shared with previous JMP disable/unconfigure
                    self.writeRam(channel, ProSLIC_CommonRamAddrs.BLOB_ID.value, blob.id)
                    self.logger.info(f"Blob loaded with id={hex(blob.id)}")

                # Next step is shared between chan0 and chan1
                self.configureBlob(channel, blob.configuration)                

                if channel == 0:
                    # Verify if the blob has all been sent correctly
                    self.verifyBlob(channel, blob)

                # Enable blob (finally)?
                self.writeRegister(channel, ProSLIC_CommonREGs.JMPEN.value, 0x01)
                self.logger.info(f"Blob enabled on chan = {channel}")
            except BlobVerifyError as e:
                raise e
            except BlobInvalidError as e:
                raise e
            except Exception as e:
                self.logger.error("Unexpected error while loading blob.")
                self.logger.error(e)
                raise BlobUploadError(self, blob.id)

        return True

    def configureJMPBlob(self, channel, regJMPs, ramJMPs):
        # Iterate through the configuration and configure the registers
        for idx, value in enumerate(regJMPs):
            self.writeRegister(
                channel, ProSLIC_CommonREGs.JMP0LO.value + idx, value)

        # More unknown stuff but *seems* related to JMP regs
        # Iterate through the configuration and configure the registers
        for idx, value in enumerate(ramJMPs):
            self.writeRam(
                channel, ProSLIC_CommonRamAddrs.BLOB_JMP_TABLE2.value + idx, value)
        
        self.logger.info(f"Blob JMP table loaded! chan={channel}")
        return True

    def configureBlob(self, channel, configuration):
        # Iterate through the configuration and configure the registers
        for reg, value in configuration.items():
            self.writeRam(channel, reg, value)

        self.logger.info(f"Blob configured! chan={channel}")
        return True

    def loadBlobData(self, channel, blob):
        if len(blob.data) == 0:
            raise BlobInvalidError(self, blob)

        # We suppose this is a auto increment register
        # if we read it after each write it get auto-incremented.
        self.writeRam(
            channel, ProSLIC_CommonRamAddrs.BLOB_DATA_ADDR.value, 0x00)

        for data in blob.data:
            self.writeRam(
                channel, ProSLIC_CommonRamAddrs.BLOB_DATA_DATA.value, data)

        # Signaling write completed
        self.writeRegister(channel, ProSLIC_CommonREGs.RAM_ADDR_HI.value, 0x00)

        self.logger.info(f"Blob data loaded! chan={channel}")
        return True
    
    def verifyBlob(self, channel, blob):

        # TODO - More stuff to check later
        self.verifyBlobData(channel, blob)        
        # verify JMP table
        # verify Blob configuration

        self.logger.info(f"Blob load verified! chan={channel}")
        return True

    def verifyBlobData(self, channel, blob):
        correct = True

        # No patch to verify return OK?
        if len(blob.data) == 0:
            raise BlobInvalidError(self, blob)

        # Disable blob (before reading)?
        self.writeRegister(channel, ProSLIC_CommonREGs.JMPEN.value, 0x00)

        self.writeRam(
            channel, ProSLIC_CommonRamAddrs.BLOB_DATA_ADDR.value, 0x00)

        for idx, data in enumerate(blob.data):
            readData = self.readRam(
                channel, ProSLIC_CommonRamAddrs.BLOB_DATA_DATA.value)
            if readData != data:
                self.logger.debug(f"Blob data mismatch: expected = {hex(data)}, received = {hex(readData)} offset = {idx}")
                correct = False
                break

        # Signaling read completed
        self.writeRegister(channel, ProSLIC_CommonREGs.RAM_ADDR_HI.value, 0x00)

        # Do we have to do something if the blob is wrong?
        if not correct:
            raise BlobVerifyError(self, blob.id)

        self.logger.info(f"Blob data verified! chan={channel}")
        return True

    def calibrate(self, data):
        # Validate data array to have correct length
        if len(data) > 4:
            self.logger.debug(f"Invalid calibration data of len={len(data)} expected={4}")
            raise InvalidCalibrationError()

        # Run for each channel one after another
        for channel in range(self.numChannels):
            for idx, value in enumerate(data):
                reg = ProSLIC_CommonREGs.CALR0.value + idx
                # self.logger.debug(f"Writing cal in register chan={channel} reg={hex(reg)} idx={idx}")
                self.writeRegister(channel, reg, value)

        # Await calibration (random value attempt)
        # Fixme timeout might be better
        # self.logger.debug(f"Waiting for calibration to complete")
        count = 5 * PROSLIC_RETRIES
        calibrating = True
        while count > 0 and calibrating:
            count -= 1
            for channel in range(self.numChannels): 
                data = self.readRegister(channel, ProSLIC_CommonREGs.CALR3.value)
                # MSB seems to be the calibration progress flag
                calibrating = data & 0x80 > 0
                # Wait a bit, spamming is useless when operation is slow 
                self.delay(15)

        # We exited the loop before running out of
        if count == 0 and calibrating:
            raise TimeoutError() # Timed out while calibrating
        elif calibrating:
            raise InvalidCalibrationError()
        else:
            return True     

    # FIXME: this shoudld pass a configuration object or something to apply
    # binary had lot of pointers, data was probably loaded from a struct.
    @abstractmethod
    def configure(self, channel = 0):
        pass

    @abstractmethod
    def enableDCDCRegulator(self, channel = 0):
        pass

    @abstractmethod
    def configureDCFeed(self, channel):
        pass

    @abstractmethod
    def configureRinger(self, channel):
        pass

    @abstractmethod
    def configureZsynth(self, channel, lineType: LineTermination):
        pass
    
    # FIXME: this shoudld pass a configuration object or something to apply
    # binary had lot of pointers, data was probably loaded from a struct.
    @abstractmethod
    def configurePCM(self, channel, format: AudioPCMFormat):
        pass
            
    # FIXME: use ghidra to decompile method
    def setPCMTimeslot(self, channel, slot=0):
        # 2025 Ghidra: Chip follow PCM-A timings, data is send/received after
        # 1 clk pulse the chip seems to support only 16-bit of data per channel.
        # So the register value is calculated as (16 * timeslot) + 1
        # This means slot 0 has a value of 1 while slot 1 has a value of 17.
        delay = (16 * slot) + 1

        # The "delay" is 10bit, 8 on PCMTXLO, 2 on lowest bits of PCMTXHI
        self.writeRegister(channel, ProSLIC_CommonREGs.PCMTXLO.value, delay)

        # 2025 Ghidra: this masked or something no idea, see configurePCM() for 
        # the special bit (4), only alter lowest 2 bits
        valueTXHI = self.readRegister(channel, ProSLIC_CommonREGs.PCMTXHI.value)        
        self.writeRegister(channel, ProSLIC_CommonREGs.PCMTXHI.value,
            (valueTXHI & 0xFC) | (delay << 8 & 0x03))

        # Repeat for RX
        self.writeRegister(channel, ProSLIC_CommonREGs.PCMRXLO.value, delay)

        valueRXHI = self.readRegister(channel, ProSLIC_CommonREGs.PCMRXHI.value)
        self.writeRegister(channel, ProSLIC_CommonREGs.PCMRXHI.value,
            (valueRXHI & 0xFC) | (delay << 8 & 0x03))

        pass
        
    def enablePCM(self, channel):
        pcmMode = self.readRegister(channel, ProSLIC_CommonREGs.PCMMODE.value)

        # 2025 Ghidra: no mask only bitset
        self.writeRegister(
            channel, ProSLIC_CommonREGs.PCMMODE.value, pcmMode | 0x10)
        
    def getHookState(self, channel = 0):
        value = self.readRegister(channel, ProSLIC_CommonREGs.LCRRTP.value)
        self.logger.debug(f"Hook register read value={hex(value)}")
        if value & 0x02:
            return False
        return True
        
    def setLineFeed(self, channel, state: Linefeed):
        valueAuto = self.readRegister(channel, ProSLIC_CommonREGs.AUTO.value)        
        valueLineFeed = self.readRegister(channel, ProSLIC_CommonREGs.LINEFEED.value)

        # State 4 is ringing, why is it special?
        # Already RINGING nothing to do
        if state == Linefeed.RINGING and valueLineFeed & 0x0F == Linefeed.RINGING.value:
            # Current state and new state are equal and RINGING
            return False
        # Not sure what this mess is!
        # 4 top bits seems to be old state and 4 low bits is current state.
        # if so when old state was RINGING and new state is NOT do nothing?
        elif (valueLineFeed & 0xF0) == (Linefeed.RINGING.value << 4) and (valueLineFeed & 0xF) != Linefeed.RINGING.value:         
            return False
        # New state is RINGING and old wasn't
        elif state == Linefeed.RINGING and valueLineFeed & 0x0F == Linefeed.RINGING.value:
            # FIXME: original binary has some calls to IRQEN1 register. unknown trigger condition
            # self.writeRegister(
            #     channel, ProSLIC_CommonREGs.IRQEN1.value, valIRQ & ~0x80)
            
            self.writeRegister(
                channel, ProSLIC_CommonREGs.LINEFEED.value, state.value)
            return False       
        else:
            # Supposing mask is 0xFB: 0x3f become 3b as captured
            self.writeRegister(channel, ProSLIC_CommonREGs.AUTO.value, valueAuto & 0xFB)
            self.writeRegister(channel, ProSLIC_CommonREGs.LINEFEED.value, state.value)
            # Restore old AUTO value
            self.writeRegister(channel, ProSLIC_CommonREGs.AUTO.value, valueAuto)

            # This is setting a value from a struct, unknown
            # self.writeRegister(
            #     channel, ProSLIC_CommonREGs.IRQEN1.value, valIRQ)

    def startRing(self, channel = 0):
        self.setLineFeed(channel, Linefeed.RINGING.value)

    def stopRing(self, channel = 0):
        self.setLineFeed(channel, Linefeed.IDLE.value)
        
    def setLoopback(self, channel, mode: LoopbackMode):
        regTemp = self.readRegister(channel, ProSLIC_CommonREGs.LOOPBACK.value)
        newValue = regTemp

        if mode == LoopbackMode.NONE:
            newValue &= ~(0x11)
        elif mode == LoopbackMode.LOOPBACK_A:
            newValue |= 1
        elif mode == mode == LoopbackMode.LOOPBACK_B:
            newValue |= 0x10
        else:
            # FIXME: throw InvalidArgument exception
            return False

        if newValue != regTemp:
            self.writeRegister(channel, ProSLIC_CommonREGs.LOOPBACK.value, newValue)
            return True
        return False
    
    # FIXME: 2025 Ghidra: part specific function, global wrapper method exist
    @abstractmethod
    def enableIRQ(self, channel = 0):
       return False
    
    @abstractmethod
    def disableIRQ(self, channel = 0):
        return False

    def getInterruptChannels(self, pendingIRQ = None) -> List[Tuple[int, int]]:
        channels = []

        # Try to read status if a provided value is not set
        if pendingIRQ == None:
            # IRQ0 is shared between channels, so read from Channel 0
            pendingIRQ = self.readRegister(0, ProSLIC_CommonREGs.IRQ0.value)

        # No IRQ raised return empty
        if not pendingIRQ:
            return []
        
        self.logger.debug(f"Raised IRQ0: {hex(pendingIRQ)}")
        
        # Process IRQ masks
        if pendingIRQ & 0x0F:
            channels.append((0, pendingIRQ & 0x0F))
        if pendingIRQ & 0xF0:
            channels.append((1, pendingIRQ & 0xF0 >> 4))

        return channels       

    def handleIRQ(self, channel, pendingRegisters):
        flags = []

        # Mask pendingRegisters, we assume shift already happened
        # pendingRegisters contains what register has a IRQ that is pending
        pendingRegisters = pendingRegisters & 0x0F
        if not pendingRegisters:
            return flags
            
        self.logger.debug(f"Pending registers: {hex(pendingRegisters)}")

        try:
            # value = self.readRegister(channel, ProSLIC_CommonREGs.IRQ2.value)
            # if value & ProSLIC_IRQ2.IRQ_LOOP_STATUS.value:
            #     if device.getHookState():
            #         logger.info(f"On Hook channel={channel}")
            #     else:
            #         logger.info("Off Hook channel={channel}")

            # Skipping IRQ as it is user set (firmware dependent?)
            register_enums = [
                ProSLIC_CommonREGs.IRQ1,
                ProSLIC_CommonREGs.IRQ2,
                ProSLIC_CommonREGs.IRQ3,
            ]
            interrupt_masks = [ProSLIC_IRQ1, ProSLIC_IRQ2, ProSLIC_IRQ3]
            for register, register_masks in zip(register_enums, interrupt_masks):
                # value = 0x00
                # # Read IRQn Register only when a previus IRQ0 states has an pending interrupt      
                # if pendingRegisters & (1 << idx):
                value = self.readRegister(channel, register.value)

                # Skip mapping if no flags are present
                if not value:
                    continue

                for irq_mask in register_masks:
                    # Flag is not set, skip to next mapped element
                    if not value & irq_mask.value:
                        continue
                    # Flag is set map to hi-level flags
                    flag = self.LOW_TO_HIGH_IRQ_MAP.get(irq_mask)
                    if flag is not None and flag not in flags:
                        flags.append(flag)

            return flags
        except Exception as e:
            self.logger.exception(e)

    def close(self):
        self.reset()

    def delay(self, ms = 100):
        time.sleep(ms / 1000)


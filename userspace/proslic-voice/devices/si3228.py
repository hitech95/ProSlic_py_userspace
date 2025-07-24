import traceback
from enum import Enum

from core.device import SiDevice
from statuses import LineTermination, AudioPCMFormat
from utils.gpio_manager import GPIOManager
from utils.resources import PROSLIC_RETRIES, ProSLIC_CommonREGs

from blobs.si32282 import Si32282Blob

class Si3228x(SiDevice):
    NAME = "PROSLIC_SI3228x"

    def __init__(self, device, irq_gpio = -1):
        super().__init__(self.NAME, device)

        self.gpioManager = None
        if irq_gpio >= 0:
            self.gpioManager = GPIOManager("/dev/gpiochip0", irq_gpio, self._interrupt)

    def setup(self):
        try:
            self.logger.debug("setup()")
            
            if self.gpioManager:
                self.gpioManager.setup()

            super().setup()

            if self.numChannels == 0:
                self.logger.debug(f"{self.NAME} No channels available, exit!")

            self.logger.debug(f"identifyChannel()")
            for channel in range(self.numChannels):
                self.getChipInfo(channel)
                self.identifyChannel(channel)

            self.logger.debug(f"identifyChannel BIS()")
            for channel in range(self.numChannels):
                self.writeRegister(channel, ProSLIC_CommonREGs.MSTRSTAT.value, 0xFF)
                # FIXME: AND all the results
                data = self.readRegister(channel, ProSLIC_CommonREGs.MSTRSTAT.value)
                data = self.identifyChannel(channel)
                data = self.testRAM(channel)

            blob = Si32282Blob()
            if not self.loadBlob(blob):
                self.logger.debug(f"Blob not loaded successully")
                return False

            self.logger.debug(f"configure()")
            for channel in range(self.numChannels):
                self.configure(channel)

            # First calibration
            self.logger.debug(f"calibrate()")
            if not self.calibrate([0x00, 0x00, 0x01, 0x80]):
                self.logger.debug(f"second calibration() failed")
                return False

            self.logger.debug(f"enableDCDCRegulator()")
            for channel in range(self.numChannels):
                self.enableDCDCRegulator(channel)

            # Second calibration
            self.logger.debug(f"calibrate()")
            if not self.calibrate([0x00, 0xC0, 0x18, 0x80]):
                self.logger.debug(f"second calibration() failed")
                return False

            for channel in range(self.numChannels):
                self.writeRegister(channel, ProSLIC_CommonREGs.ENHANCE.value, 0x10)
                self.writeRegister(channel, ProSLIC_CommonREGs.AUTO.value, 0x3F)
                self.writeRegister(channel, SI3228x_REGs.ZCAL_EN.value, 0x04)

            self.logger.debug(f"Setup done!")

            return True
        
        except Exception as e:
            self.logger.debug(f"Exception while opening")
            self.logger.debug(e)
            traceback.print_exc()
            return False
    
    def close(self):
        if self.gpioManager:
            self.gpioManager.close()
        return super().close()

    # Chip variant specific vesion add call to ENHANCE
    def getChipInfo(self, channel):
        value = super().getChipInfo(channel)

        # No idea why this is also called
        self.readRegister(channel, ProSLIC_CommonREGs.ENHANCE.value)

        return value
        
    def configure(self, channel = 0):
        data = self.enterUserMode(channel)

        # This is pure configuration stuff that we have no idea about!
        # The registers have an hardcoed value while the RAM are pointers
        # some struct abstraction was in place.
        self.writeRegister(channel, ProSLIC_CommonREGs.ENHANCE.value, 0x00)
        self.writeRegister(channel, ProSLIC_CommonREGs.AUTO.value, 0x2F)

        self.writeRam(channel, 0x2fc, 0xad000)

        self.writeRam(channel, 0x300, 0x6666635)

        self.writeRam(channel, 0x2ff, 0x3d70a20)

        self.writeRam(channel, 0x393, 0xfff0000)
        self.writeRam(channel, 0x394, 0x1999a00)
        self.writeRam(channel, 0x397, 0xf00000)
        self.writeRam(channel, 0x398, 0xf00000)
        self.writeRam(channel, 0x3ca, 0x800000)
        self.writeRam(channel, 0x3ec, 0xf18900)
        self.writeRam(channel, 0x3ed, 0x809d80)
        self.writeRam(channel, 0x3ee, 0x0)
        self.writeRam(channel, 0x3ef, 0x1a00000)

        self.writeRam(channel, 0x604, 0x400000)
        self.writeRam(channel, 0x605, 0x400000)
        self.writeRam(channel, 0x606, 0x200000)
        self.writeRam(channel, 0x609, 0x500000)
        self.writeRam(channel, 0x60a, 0x0)
        self.writeRam(channel, 0x60b, 0xa00000)
        self.writeRam(channel, 0x612, 0x0)
        self.writeRam(channel, 0x616, 0x0)
        self.writeRam(channel, 0x618, 0x200000)
        self.writeRam(channel, 0x631, 0x300000)
        self.writeRam(channel, 0x632, 0x180000)
        self.writeRam(channel, 0x633, 0x100000)
        self.writeRam(channel, 0x634, 0x12fc000)
        self.writeRam(channel, 0x635, 0xf00000)
        self.writeRam(channel, 0x636, 0xfda4000)

        self.writeRam(channel, 0x2f7, 0x7feb800)
        self.writeRam(channel, 0x2f4, 0x5b05b2)

        self.writeRam(channel, 0x3c7, 0x3a2e8ba)
        self.writeRam(channel, 0x3fa, 0x3000000)
        self.writeRam(channel, 0x3f9, 0x5000000)
        self.writeRam(channel, 0x3f5, 0x1000000)
        self.writeRam(channel, 0x3f4, 0x3700000)
        self.writeRam(channel, 0x3f3, 0x4b80200)
        self.writeRam(channel, 0x3f2, 0x823000)

        data = self.readRegister(channel, 0x44)
        # This is reading and doing some ops with the data
        #  its a case that the data is the same.
        # decopilation: (data & 0xF9) | 0x60
        self.writeRegister(channel, 0x44, (data & 0xF9) | 0x60)

        self.writeRegister(channel, ProSLIC_CommonREGs.PDN.value, 0x80)

        self.writeRam(channel, 0x215, 0x71eb851)
        self.writeRam(channel, 0x272, 0x723f235)
        self.writeRam(channel, 0x273, 0x57a9804)
        self.writeRam(channel, 0x396, 0x36000)
        self.writeRam(channel, 0x650, 0x1100000)
        self.writeRam(channel, 0x3cd, 0xffffff)
        self.writeRam(channel, 0x3ce, 0xa18937)
        self.writeRam(channel, 0x3cf, 0xe49ba5)

        self.writeRam(channel, 0x204, 0x10038d)
        self.writeRam(channel, 0x201, 0x4eddb9)
        self.writeRam(channel, 0x202, 0x806d6)
        self.writeRam(channel, 0x205, 0x10059f)
        self.writeRam(channel, 0x2c4, 0xf0000)
        self.writeRam(channel, 0x2c5, 0x106240)

        data = self.readRam(channel, 0x627)
        self.writeRam(channel, 0x627, data & 0x0BFFFFFF)

        self.writeRam(channel, 0x669, 0x200000)
        self.writeRam(channel, 0x66b, 0x0)
        self.writeRam(channel, 0x61d, 0xc00000)
        self.writeRam(channel, 0x2ee, 0x206280)
        self.writeRam(channel, 0x663, 0x0)
        self.writeRam(channel, 0x3cb, 0x1f00000)
        self.writeRam(channel, 0x3cc, 0x51eb80)
        self.writeRam(channel, 0x611, 0x0)
        self.writeRam(channel, 0x35c, 0xa00000)

        return True
    
    # There is a struct that is deciding what logic to follow
    # match with 0x01 has more logic, implementing sniffed bus data
    # FIXME: 2025 Ghidra: part specific function, global wrapper method exist
    def enableDCDCRegulator(self, channel):

        # We suppose that it is always the same logic when reading 0x7E
        self.enterUserMode(channel)
            
        # This block here is repeated for each channel so its probably is a shared method
        data = self.readRam(channel, 0x602)

        # We have to do some sort of gating but we dont know how assuming 0x00
        # 2025 Ghidra: it seems gate is 0x100000
        if not data & 0x100000:
            return False

        ############################
        # Mode 0x01 implementation #
        ############################
        
        self.writeRam(channel, 0x60c, 0x0)

        self.writeRegister(channel, ProSLIC_CommonREGs.LINEFEED.value, 0x0)

        enhance = self.readRegister(channel, ProSLIC_CommonREGs.ENHANCE.value)
        # We are obviusly doing something here with value readed
        # 2025 Ghidra: mask is 0x07
        self.writeRegister(channel, ProSLIC_CommonREGs.ENHANCE.value, enhance & 0x07)

        self.writeRam(channel, 0x602, 0x700000)
        self.writeRam(channel, 0x613, 0x100000)

        # From capture we have some delay here
        self.delay(15)

        self.writeRam(channel, 0x602, 0x600000)

        # From capture we have some delay here (power up ?)
        self.delay(50)

        expected = self.readRam(channel, 0x2ff)
        data = self.readRam(channel, 0x3)

        # We are for sure checking something here if condition
        # not met probably an hard halt here.
        # 2025 Ghidra: Short circuit failure when 1/2 expected value
        if data < (expected / 2):
            self.writeRam(channel, 0x602, 0x300000)
            # FIXME: more is done on decompile binary. Not fully decompiled.
            self.logger.debug(f"Short circuit detected on chan = {channel}")
            # FIXME: exception might be better as we are using python
            return False

        self.writeRam(channel, 0x60f, 0x0)
        self.writeRam(channel, 0x602, 0x400000)

        self.writeRegister(channel, ProSLIC_CommonREGs.ENHANCE.value, enhance)
        self.delay(50)

        #############################
        # Other Mode implementation #
        #############################

        # 2025 Ghidra: some sort of check + timeout
        # More read of stuff no idea what is doing
        expected = self.readRam(channel, 0x2ff)
        data = 0
        count = 5 * PROSLIC_RETRIES
        while count > 0 and ( data < expected - 0x51EB82):
            count -= 1
            data = self.readRam(channel, 0x3)
            if data & 0x10000000:
                data |= 0xF0000000

        if count > 0:
            return True

        # This then seems to be a shutdown command
        self.writeRam(channel, 0x602, 0x300000)
        self.logger.debug(f"Power up timeout on chan = {channel}")
        # FIXME: exception might be better as we are using python
        return False

    # According to decopiled dragino2-si3217x.o this should be Si3228_DCFeedSetup()
    # Takes a preset_id, check if this depends on other variable in D2 as on dragino2
    # This probably configure the DC-AC converter and mosdulation for the ring.
    # Not to be confised with other ring signals lice CID or tones.
    def configureDCFeed(self, channel):
        lineFeed = self.readRegister(channel, SI3228x_REGs.LINEFEED.value)
        self.writeRegister(channel, SI3228x_REGs.LINEFEED.value, 0x00)

        self.writeRam(channel, 0x27a, 0x1d999d52)
        self.writeRam(channel, 0x27b, 0x1f26f6a1)
        self.writeRam(channel, 0x27c, 0x40a0e0)
        self.writeRam(channel, 0x27e, 0x1ad888e8)
        self.writeRam(channel, 0x27f, 0x1cfbde56)
        self.writeRam(channel, 0x280, 0x5dfabcb)
        self.writeRam(channel, 0x281, 0x50d2839)
        self.writeRam(channel, 0x282, 0x3fe7f0f)
        self.writeRam(channel, 0x283, 0xf7a560)
        self.writeRam(channel, 0x284, 0x6b0532)
        self.writeRam(channel, 0x285, 0x2f737c)
        self.writeRam(channel, 0x355, 0x5b0afb)
        self.writeRam(channel, 0x354, 0x6d4060)
        self.writeRam(channel, 0x2bd, 0x8000)
        self.writeRam(channel, 0x35a, 0x48d595)
        self.writeRam(channel, 0x35b, 0x3fbae2)
        self.writeRam(channel, 0x2be, 0x8000)
        self.writeRam(channel, 0x356, 0xf0000)
        self.writeRam(channel, 0x357, 0x80000)
        self.writeRam(channel, 0x358, 0x140000)
        self.writeRam(channel, 0x359, 0x140000)
        self.writeRam(channel, 0x2ec, 0x1ba5e35)
        self.writeRam(channel, 0x2f0, 0x51eb85)
        self.writeRam(channel, 0x2ef, 0x415f45)

        self.writeRegister(channel, ProSLIC_CommonREGs.LINEFEED.value, lineFeed)


    # According to decopiled dragino2-si3217x.o this should be Si3228_RingSetup()
    # Takes a preset_id. 
    # TODO: check if this depends on other variable in D2 as on dragino2
    # This probably configure the DC-AC converter and mosdulation for the ring.
    # Not to be confised with other ring signals lice CID or tones.
    def configureRinger(self, channel):
        self.writeRam(channel, 0x2f3, 0x40000)
        self.writeRam(channel, 0x34c, 0x7e6c000)
        self.writeRam(channel, 0x34d, 0x27f1a3)
        self.writeRam(channel, 0x34e, 0x0)
        self.writeRam(channel, 0x34b, 0x0)
        self.writeRam(channel, 0x27d, 0x15e5200e)
        self.writeRam(channel, 0x35c, 0x6c94d6)
        self.writeRam(channel, 0x350, 0x614e73)

        self.writeRam(channel, 0x34f, 0xfffffff)
        self.writeRam(channel, 0x352, 0x8000)
        self.writeRam(channel, 0x351, 0x8000)
        self.writeRam(channel, 0x2f1, 0x51eb82)
        self.writeRam(channel, 0x380, 0x0)
        self.writeRam(channel, 0x300, 0x59cda16)

        self.writeRegister(channel, SI3228x_REGs.RINGTALO.value, 0x80)
        self.writeRegister(channel, SI3228x_REGs.RINGTAHI.value, 0x3e)
        self.writeRegister(channel, SI3228x_REGs.RINGTILO.value, 0x0)
        self.writeRegister(channel, SI3228x_REGs.RINGTIHI.value, 0x7d)

        self.writeRam(channel, 0x398, 0x1893740)

        self.writeRegister(channel, SI3228x_REGs.RINGCON.value, 0x80)
        self.writeRegister(channel, SI3228x_REGs.USERSTAT.value, 0x0)

        self.writeRam(channel, 0x2ed, 0x2ce6d0b)
        self.writeRam(channel, 0x1e2, 0x2ce6d0b)
        self.writeRam(channel, 0x1e3, 0x3126e8)

        self.enterUserMode(channel)

        self.writeRam(channel, 0x618, 0x200000)
        self.writeRam(channel, 0x1b2, 0x0)

        pass
    
    # According to decopiled dragino2-si3217x.o this should be Si3228_ZsynthSetup()
    # Takes a preset_id, check if this depends on other variable in D2 as on dragino2
    # 2025 Ghidra: hardcoded as preset 1 in D2, probably a #define at compile time,
    # other cases valus might be present.
    def configureZsynth(self, channel, lineType: LineTermination):
        lineFeed = self.readRegister(channel, ProSLIC_CommonREGs.LINEFEED.value)
        self.writeRegister(channel, ProSLIC_CommonREGs.LINEFEED.value, 0x00)

        # FIXME: we should load different data for the different PSTN standards
        if lineType == LineTermination.TBR21:
            pass
        elif lineType == LineTermination.BT3:
            pass
        elif lineType == LineTermination.TN12:
            pass
        else:
            pass

        # Supposing this is for LineTermination.TBR21
        self.writeRam(channel, 0x21c, 0x750e500)
        self.writeRam(channel, 0x21d, 0x1fc70280)
        self.writeRam(channel, 0x21e, 0xba980)
        self.writeRam(channel, 0x21f, 0x1ffd2880)

        self.writeRam(channel, 0x222, 0xa8e2380)
        self.writeRam(channel, 0x223, 0x1b905280)
        self.writeRam(channel, 0x224, 0x847700)
        self.writeRam(channel, 0x225, 0x1fdafa00)

        self.writeRam(channel, 0x233, 0x2c8880)
        self.writeRam(channel, 0x234, 0x1f630d80)
        self.writeRam(channel, 0x235, 0x27f7980)
        self.writeRam(channel, 0x236, 0x1f3ad200)
        self.writeRam(channel, 0x237, 0x40b8680)
        self.writeRam(channel, 0x238, 0x1f414d00)
        self.writeRam(channel, 0x239, 0x1427b00)
        self.writeRam(channel, 0x23a, 0x208200)
        self.writeRam(channel, 0x23b, 0x26ae00)
        self.writeRam(channel, 0x23c, 0x1fd71680)
        self.writeRam(channel, 0x23d, 0xc8edb00)
        self.writeRam(channel, 0x23e, 0x1b688a00)

        self.writeRam(channel, 0x290, 0xd7fe800)
        self.writeRam(channel, 0x291, 0x1a7f1a80)
        self.writeRam(channel, 0x28e, 0x96fe00)
        self.writeRam(channel, 0x28d, 0x1f657980)
        self.writeRam(channel, 0x28f, 0x35500)

        self.writeRegister(channel, SI3228x_REGs.RA.value, 0xb4)

        self.writeRam(channel, 0x220, 0x8000000)
        self.writeRam(channel, 0x38a, 0x1106b80)
        self.writeRam(channel, 0x221, 0x1106b80)
        self.writeRam(channel, 0x292, 0x7bc8400)
        self.writeRam(channel, 0x293, 0x18437c80)
        self.writeRam(channel, 0x294, 0x7790880)

        # Values below are generated in a child function
        self.writeRam(channel, 0x220, 0x7fffd28)
        self.writeRam(channel, 0x21c, 0x750e4f0)
        self.writeRam(channel, 0x21d, 0x1fc70610)
        self.writeRam(channel, 0x21e, 0xba860)
        self.writeRam(channel, 0x21f, 0x1ffd2970)

        self.writeRam(channel, 0x38a, 0x1106a48)
        self.writeRam(channel, 0x221, 0x1106a48)
        self.writeRam(channel, 0x222, 0xa8e2218)
        self.writeRam(channel, 0x223, 0x1b905588)
        self.writeRam(channel, 0x224, 0x847628)
        self.writeRam(channel, 0x225, 0x1fdafb70)

        # FIXME - What to do in case of failure?
        # Re-calibrate, something has changed!
        self.writeRegister(channel, ProSLIC_CommonREGs.CALR0.value, 0x00)
        self.writeRegister(channel, ProSLIC_CommonREGs.CALR1.value, 0x40)
        self.writeRegister(channel, ProSLIC_CommonREGs.CALR2.value, 0x00)
        self.writeRegister(channel, ProSLIC_CommonREGs.CALR3.value, 0x80)

        count = 5 * PROSLIC_RETRIES
        calibrating = True
        while count > 0 and calibrating:
            count -= 1    
            data = self.readRegister(channel, ProSLIC_CommonREGs.CALR3.value)
            # MSB seems to be the calibration progress flag
            calibrating = data & 0x80 > 0
            # Wait a bit, spamming is useless when operation is slow 
            self.delay(15)

        if not count:
            return False  # Timed out
        
        self.writeRegister(channel, ProSLIC_CommonREGs.LINEFEED.value, lineFeed)
        return True
    
    def configurePCM(self, channel, format: AudioPCMFormat):
        valPMCon = self.readRegister(channel, SI3228x_REGs.PMCON.value)

        # 2025 Ghidra: this is used to skip the init below
        # if valPMCon & 0x01 and preset condition:
        # pass
        # elif preset condition no rea flag :
        # many memory writes
        # else:

        valDigCon = self.readRegister(channel, SI3228x_REGs.DIGCON.value)

        # 2025 Ghidra: mask ~0x0C
        self.writeRegister(channel, SI3228x_REGs.DIGCON.value, valDigCon & (~0x0C))

        # More unknown binary data :(
        self.writeRam(channel, 0x206, 0x3538e80)
        self.writeRam(channel, 0x207, 0x3538e80)
        self.writeRam(channel, 0x208, 0x1aa9100)
        self.writeRam(channel, 0x209, 0x216d100)
        self.writeRam(channel, 0x20a, 0x2505400)
        self.writeRam(channel, 0x20b, 0x216d100)
        self.writeRam(channel, 0x20c, 0x2cb8100)
        self.writeRam(channel, 0x20d, 0x1d7fa500)
        self.writeRam(channel, 0x20e, 0x2cd9b00)
        self.writeRam(channel, 0x20f, 0x1276d00)
        self.writeRam(channel, 0x210, 0x2cd9b00)
        self.writeRam(channel, 0x211, 0x2335300)
        self.writeRam(channel, 0x212, 0x19d5f700)
        self.writeRam(channel, 0x226, 0x6a71d00)
        self.writeRam(channel, 0x227, 0x6a71d00)
        self.writeRam(channel, 0x228, 0x1aa9100)
        self.writeRam(channel, 0x229, 0x216d100)
        self.writeRam(channel, 0x22a, 0x2505400)
        self.writeRam(channel, 0x22b, 0x216d100)
        self.writeRam(channel, 0x22c, 0x2cb8100)
        self.writeRam(channel, 0x22d, 0x1d7fa500)
        self.writeRam(channel, 0x22e, 0x2cd9b00)
        self.writeRam(channel, 0x22f, 0x1276d00)
        self.writeRam(channel, 0x230, 0x2cd9b00)
        self.writeRam(channel, 0x231, 0x2335300)
        self.writeRam(channel, 0x232, 0x19d5f700)

        valEnhance = self.readRegister(channel, SI3228x_REGs.ENHANCE.value)

        # 2025 Ghidra - Mask is ~0x01
        self.writeRegister(channel, SI3228x_REGs.ENHANCE.value, valEnhance & (~0x01))


        # 2025 Ghidra: reading 5 bytes of data/settings from a struct + offset
        # same as other cases, array structs for different presets
        # byte(3) for previous IF condition, exception print "wideband mode"
        
        # byte (0) | byte(2) << 5 | byte(4) << 2
        
        # FIXME: we have only implemented the format
        self.writeRegister(channel, SI3228x_REGs.PCMMODE.value, format.value & 0x03)
        valPCMTXHI = self.readRegister(channel, SI3228x_REGs.PCMTXHI.value)

        # 2025 Ghidra: masked with 0x03 put in OR with other data (shifted)
        # This is byte(3)
        data = 0x00
        self.writeRegister(
            channel, SI3228x_REGs.PCMTXHI.value,  (valPCMTXHI & 0x03) | data << 4)

    def enableIRQ(self, channel = 0):
        # Clear current IRQs
        self.readRegister(channel, SI3228x_REGs.IRQ1.value)
        self.readRegister(channel, SI3228x_REGs.IRQ2.value)
        self.readRegister(channel, SI3228x_REGs.IRQ3.value)
        self.readRegister(channel, SI3228x_REGs.IRQ4.value)

        # Enable them
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN1.value, 0x50)
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN2.value, 0x13)
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN3.value, 0x07)
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN4.value, 0x00)
    
    def disableIRQ(self, channel):
        # Enable them
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN1.value, 0x00)
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN2.value, 0x00)
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN3.value, 0x00)
        self.writeRegister(
            channel, SI3228x_REGs.IRQEN4.value, 0x00)

class SI3228x_REGs(Enum):
    ID  =  0
    RESET  =  1
    MSTREN  =  2
    MSTRSTAT  =  3
    RAMSTAT  =  4
    RAM_ADDR_HI  =  5
    RAM_DATA_B0  =  6
    RAM_DATA_B1  =  7
    RAM_DATA_B2  =  8
    RAM_DATA_B3  =  9
    RAM_ADDR_LO  =  10
    PCMMODE  =  11
    PCMTXLO  =  12
    PCMTXHI  =  13
    PCMRXLO  =  14
    PCMRXHI  =  15
    IRQ  =  16
    IRQ0  =  17
    IRQ1  =  18
    IRQ2  =  19
    IRQ3  =  20
    IRQ4  =  21
    IRQEN1  =  22
    IRQEN2  =  23
    IRQEN3  =  24
    IRQEN4  =  25
    CALR0  =  26
    CALR1  =  27
    CALR2  =  28
    CALR3  =  29
    LINEFEED  =  30
    POLREV  =  31
    SPEEDUP_DIS  =  32
    SPEEDUP  =  33
    LCRRTP  =  34
    OFFLOAD  =  35
    BATSELMAP  =  36
    BATSEL  =  37
    RINGCON  =  38
    RINGTALO  =  39
    RINGTAHI  =  40
    RINGTILO  =  41
    RINGTIHI  =  42
    LOOPBACK  =  43
    DIGCON  =  44
    RA  =  45
    ZCAL_EN  =  46
    ENHANCE  =  47
    OMODE  =  48
    OCON  =  49
    O1TALO  =  50
    O1TAHI  =  51
    O1TILO  =  52
    O1TIHI  =  53
    O2TALO  =  54
    O2TAHI  =  55
    O2TILO  =  56
    O2TIHI  =  57
    FSKDAT  =  58
    FSKDEPTH  =  59
    TONDTMF  =  60
    TONDET  =  61
    TONEN  =  62
    GCI_CI  =  63
    GLOBSTAT1  =  64
    GLOBSTAT2  =  65
    USERSTAT  =  66
    GPIO_CFG1 = 68
    DIAG1  =  71
    DIAG2  =  72
    CM_CLAMP  =  73
    DIAG3  =  74
    PMCON  =  75
    PCLK_FAULT_CNTL  =  76
    REG77  =  77
    REG78  =  78
    REG79  =  79
    AUTO  =  80
    JMPEN  =  81
    JMP0LO  =  82
    JMP0HI  =  83
    JMP1LO  =  84
    JMP1HI  =  85
    JMP2LO  =  86
    JMP2HI  =  87
    JMP3LO  =  88
    JMP3HI  =  89
    JMP4LO  =  90
    JMP4HI  =  91
    JMP5LO  =  92
    JMP5HI  =  93
    JMP6LO  =  94
    JMP6HI  =  95
    JMP7LO  =  96
    JMP7HI  =  97
    PDN  =  98
    PDN_STAT  =  99
    USERMODE_ENABLE = 12

class SI3228x_RAMs(Enum):
    IRNGNG_SENSE = 0  # 0x0000
    MADC_VTIPC = 1  # 0x0001
    MADC_VRINGC = 2  # 0x0002
    MADC_VBAT = 3  # 0x0003
    MADC_VLONG = 4  # 0x0004
    UNUSED5 = 5  # 0x0005
    MADC_VDC = 6  # 0x0006
    MADC_ILONG = 7  # 0x0007
    MADC_ITIP = 8  # 0x0008
    MADC_IRING = 9  # 0x0009
    MADC_ILOOP = 10  # 0x000A
    VDIFF_SENSE = 11  # 0x000B
    VTIP = 12  # 0x000C
    VRING = 13  # 0x000D
    P_Q1_D = 14  # 0x000E
    INIT_GUESS = 15  # 0x000F
    Y1 = 16  # 0x0010
    Y2 = 17  # 0x0011
    Y3 = 18  # 0x0012
    UNUSED19 = 19  # 0x0013
    P_Q1 = 20  # 0x0014
    DIAG_EX1 = 21  # 0x0015
    DIAG_EX2 = 22  # 0x0016
    DIAG_LPF_MADC = 23  # 0x0017
    DIAG_DMM_I = 24  # 0x0018
    DIAG_DMM_V = 25  # 0x0019
    OSC1FREQ = 26  # 0x001A
    OSC1AMP = 27  # 0x001B
    OSC1PHAS = 28  # 0x001C
    OSC2FREQ = 29  # 0x001D
    OSC2AMP = 30  # 0x001E
    OSC2PHAS = 31  # 0x001F
    TESTB0_1 = 32  # 0x0020
    TESTB1_1 = 33  # 0x0021
    TESTB2_1 = 34  # 0x0022
    TESTA1_1 = 35  # 0x0023
    TESTA2_1 = 36  # 0x0024
    TESTB0_2 = 37  # 0x0025
    TESTB1_2 = 38  # 0x0026
    TESTB2_2 = 39  # 0x0027
    TESTA1_2 = 40  # 0x0028
    TESTA2_2 = 41  # 0x0029
    TESTB0_3 = 42  # 0x002A
    TESTB1_3 = 43  # 0x002B
    TESTB2_3 = 44  # 0x002C
    TESTA1_3 = 45  # 0x002D
    TESTA2_3 = 46  # 0x002E
    TESTPKO = 47  # 0x002F
    TESTABO = 48  # 0x0030
    TESTWLN = 49  # 0x0031
    TESTAVBW = 50  # 0x0032
    TESTPKFL = 51  # 0x0033
    TESTAVFL = 52  # 0x0034
    TESTPKTH = 53  # 0x0035
    TESTAVTH = 54  # 0x0036
    DAC_IN_SYNC1 = 55  # 0x0037
    BYPASS_REG = 56  # 0x0038
    LCRMASK_CNT = 57  # 0x0039
    DAC_IN_SYNC = 58  # 0x003A
    TEMP = 59  # 0x003B
    TEMP_ISR = 60  # 0x003C
    P_Q2 = 61  # 0x003D
    P_Q3 = 62  # 0x003E
    P_Q4 = 63  # 0x003F
    P_Q5 = 64  # 0x0040
    P_Q6 = 65  # 0x0041
    ILOOP_FILT = 66  # 0x0042
    ILONG_FILT = 67  # 0x0043
    VBAT_FILT = 68  # 0x0044
    VDIFF_FILT = 69  # 0x0045
    VCM_FILT = 70  # 0x0046
    VBAT_CNT = 71  # 0x0047
    V_VLIM_SCALED = 72  # 0x0048
    V_VLIM_TRACK = 73  # 0x0049
    V_VLIM_MODFEED = 74  # 0x004A
    DIAG_P_OUT = 75  # 0x004B
    DIAG_COUNT = 76  # 0x004C
    ROW0_MAG = 77  # 0x004D
    ROW1_MAG = 78  # 0x004E
    ROW2_MAG = 79  # 0x004F
    ROW3_MAG = 80  # 0x0050
    COL0_MAG = 81  # 0x0051
    COL1_MAG = 82  # 0x0052
    COL2_MAG = 83  # 0x0053
    COL3_MAG = 84  # 0x0054
    ROW0_2ND_Y1 = 85  # 0x0055
    ROW1_2ND_Y1 = 86  # 0x0056
    ROW2_2ND_Y1 = 87  # 0x0057
    ROW3_2ND_Y1 = 88  # 0x0058
    COL0_2ND_Y1 = 89  # 0x0059
    COL1_2ND_Y1 = 90  # 0x005A
    COL2_2ND_Y1 = 91  # 0x005B
    COL3_2ND_Y1 = 92  # 0x005C
    ROW0_2ND_Y2 = 93  # 0x005D
    ROW1_2ND_Y2 = 94  # 0x005E
    ROW2_2ND_Y2 = 95  # 0x005F
    ROW3_2ND_Y2 = 96  # 0x0060
    COL0_2ND_Y2 = 97  # 0x0061
    COL1_2ND_Y2 = 98  # 0x0062
    COL2_2ND_Y2 = 99  # 0x0063
    COL3_2ND_Y2 = 100  # 0x0064
    DTMF_IN = 101  # 0x0065
    DTMFDTF_D2_1 = 102  # 0x0066
    DTMFDTF_D1_1 = 103  # 0x0067
    DTMFDTF_OUT_1 = 104  # 0x0068
    DTMFDTF_D2_2 = 105  # 0x0069
    DTMFDTF_D1_2 = 106  # 0x006A
    DTMFDTF_OUT_2 = 107  # 0x006B
    DTMFDTF_D2_3 = 108  # 0x006C
    DTMFDTF_D1_3 = 109  # 0x006D
    DTMFDTF_OUT_3 = 110  # 0x006E
    DTMFDTF_OUT = 111  # 0x006F
    DTMFLPF_D2_1 = 112  # 0x0070
    DTMFLPF_D1_1 = 113  # 0x0071
    DTMFLPF_OUT_1 = 114  # 0x0072
    DTMFLPF_D2_2 = 115  # 0x0073
    DTMFLPF_D1_2 = 116  # 0x0074
    DTMFLPF_OUT_2 = 117  # 0x0075
    DTMF_ROW = 118  # 0x0076
    DTMFHPF_D2_1 = 119  # 0x0077
    DTMFHPF_D1_1 = 120  # 0x0078
    DTMFHPF_OUT_1 = 121  # 0x0079
    DTMFHPF_D2_2 = 122  # 0x007A
    DTMFHPF_D1_2 = 123  # 0x007B
    DTMFHPF_OUT_2 = 124  # 0x007C
    DTMF_COL = 125  # 0x007D
    ROW_POWER = 126  # 0x007E
    COL_POWER = 127  # 0x007F
    GP_TIMER = 128  # 0x0080
    SPR_INTERP_DIF = 129  # 0x0081
    SPR_INTERP_DIF_OUT = 130  # 0x0082
    SPR_INTERP_INT = 131  # 0x0083
    SPR_CNT = 132  # 0x0084
    ROW0_Y1 = 133  # 0x0085
    ROW0_Y2 = 134  # 0x0086
    ROW1_Y1 = 135  # 0x0087
    ROW1_Y2 = 136  # 0x0088
    ROW2_Y1 = 137  # 0x0089
    ROW2_Y2 = 138  # 0x008A
    ROW3_Y1 = 139  # 0x008B
    ROW3_Y2 = 140  # 0x008C
    COL0_Y1 = 141  # 0x008D
    COL0_Y2 = 142  # 0x008E
    COL1_Y1 = 143  # 0x008F
    COL1_Y2 = 144  # 0x0090
    COL2_Y1 = 145  # 0x0091
    COL2_Y2 = 146  # 0x0092
    COL3_Y1 = 147  # 0x0093
    COL3_Y2 = 148  # 0x0094
    ROWMAX_MAG = 149  # 0x0095
    COLMAX_MAG = 150  # 0x0096
    ROW0_2ND_MAG = 151  # 0x0097
    COL0_2ND_MAG = 152  # 0x0098
    ROW_THR = 153  # 0x0099
    COL_THR = 154  # 0x009A
    OSC1_Y = 155  # 0x009B
    OSC2_Y = 156  # 0x009C
    OSC1_X = 157  # 0x009D
    OSC1_COEFF = 158  # 0x009E
    OSC2_X = 159  # 0x009F
    OSC2_COEFF = 160  # 0x00A0
    RXACIIR_D2_1 = 161  # 0x00A1
    RXACIIR_OUT_1 = 162  # 0x00A2
    RXACIIR_D2_2 = 163  # 0x00A3
    RXACIIR_D1_2 = 164  # 0x00A4
    RXACIIR_OUT_2 = 165  # 0x00A5
    RXACIIR_D2_3 = 166  # 0x00A6
    RXACIIR_D1_3 = 167  # 0x00A7
    RXACIIR_OUT = 168  # 0x00A8
    RXACIIR_OUT_3 = 169  # 0x00A9
    TXACCOMB_D1 = 170  # 0x00AA
    TXACCOMB_D2 = 171  # 0x00AB
    TXACCOMB_D3 = 172  # 0x00AC
    TXACSINC_OUT = 173  # 0x00AD
    TXACHPF_D1_2 = 174  # 0x00AE
    TXACHPF_D2_1 = 175  # 0x00AF
    TXACHPF_D2_2 = 176  # 0x00B0
    TXACHPF_OUT = 177  # 0x00B1
    TXACHPF_OUT_1 = 178  # 0x00B2
    TXACHPF_OUT_2 = 179  # 0x00B3
    TXACIIR_D2_1 = 180  # 0x00B4
    TXACIIR_OUT_1 = 181  # 0x00B5
    TXACIIR_D2_2 = 182  # 0x00B6
    TXACIIR_D1_2 = 183  # 0x00B7
    TXACIIR_OUT_2 = 184  # 0x00B8
    TXACIIR_D2_3 = 185  # 0x00B9
    TXACIIR_D1_3 = 186  # 0x00BA
    TXACIIR_OUT_3 = 187  # 0x00BB
    TXACIIR_OUT = 188  # 0x00BC
    ECIIR_D1 = 189  # 0x00BD
    ECIIR_D2 = 190  # 0x00BE
    EC_DELAY1 = 191  # 0x00BF
    EC_DELAY2 = 192  # 0x00C0
    EC_DELAY3 = 193  # 0x00C1
    EC_DELAY4 = 194  # 0x00C2
    EC_DELAY5 = 195  # 0x00C3
    EC_DELAY6 = 196  # 0x00C4
    EC_DELAY7 = 197  # 0x00C5
    EC_DELAY8 = 198  # 0x00C6
    EC_DELAY9 = 199  # 0x00C7
    EC_DELAY10 = 200  # 0x00C8
    EC_DELAY11 = 201  # 0x00C9
    ECHO_EST = 202  # 0x00CA
    EC_OUT = 203  # 0x00CB
    TESTFILT_OUT_1 = 204  # 0x00CC
    TESTFILT_D1_1 = 205  # 0x00CD
    TESTFILT_D2_1 = 206  # 0x00CE
    TESTFILT_OUT_2 = 207  # 0x00CF
    TESTFILT_D1_2 = 208  # 0x00D0
    TESTFILT_D2_2 = 209  # 0x00D1
    TESTFILT_OUT_3 = 210  # 0x00D2
    TESTFILT_D1_3 = 211  # 0x00D3
    TESTFILT_D2_3 = 212  # 0x00D4
    TESTFILT_PEAK = 213  # 0x00D5
    TESTFILT_ABS = 214  # 0x00D6
    TESTFILT_MEANACC = 215  # 0x00D7
    TESTFILT_COUNT = 216  # 0x00D8
    TESTFILT_NO_OFFSET = 217  # 0x00D9
    RING_X = 218  # 0x00DA
    RING_Y = 219  # 0x00DB
    RING_INT = 220  # 0x00DC
    RING_Y_D1 = 221  # 0x00DD
    RING_DIFF = 222  # 0x00DE
    RING_DELTA = 223  # 0x00DF
    WTCHDOG_CNT = 224  # 0x00E0
    RING_WAVE = 225  # 0x00E1
    UNUSED226 = 226  # 0x00E2
    ONEKHZ_COUNT = 227  # 0x00E3
    TX2100_Y1 = 228  # 0x00E4
    TX2100_Y2 = 229  # 0x00E5
    TX2100_MAG = 230  # 0x00E6
    RX2100_Y1 = 231  # 0x00E7
    RX2100_Y2 = 232  # 0x00E8
    RX2100_MAG = 233  # 0x00E9
    TX2100_POWER = 234  # 0x00EA
    RX2100_POWER = 235  # 0x00EB
    TX2100_IN = 236  # 0x00EC
    RX2100_IN = 237  # 0x00ED
    RINGTRIP_COUNT = 238  # 0x00EE
    RINGTRIP_DC1 = 239  # 0x00EF
    RINGTRIP_DC2 = 240  # 0x00F0
    RINGTRIP_AC1 = 241  # 0x00F1
    RINGTRIP_AC2 = 242  # 0x00F2
    RINGTRIP_AC_COUNT = 243  # 0x00F3
    RINGTRIP_DC_COUNT = 244  # 0x00F4
    RINGTRIP_AC_RESULT = 245  # 0x00F5
    RINGTRIP_DC_RESULT = 246  # 0x00F6
    RINGTRIP_ABS = 247  # 0x00F7
    TXACEQ_OUT = 248  # 0x00F8
    LCR_DBI_CNT = 249  # 0x00F9
    BAT_DBI_CNT = 250  # 0x00FA
    LONG_DBI_CNT = 251  # 0x00FB
    TXACEQ_DELAY3 = 252  # 0x00FC
    TXACEQ_DELAY2 = 253  # 0x00FD
    TXACEQ_DELAY1 = 254  # 0x00FE
    RXACEQ_DELAY3 = 255  # 0x00FF
    RXACEQ_DELAY2 = 256  # 0x0100
    RXACEQ_DELAY1 = 257  # 0x0101
    RXACEQ_IN = 258  # 0x0102
    TXDCCOMB_D1 = 259  # 0x0103
    TXDCCOMB_D2 = 260  # 0x0104
    TXDCSINC_OUT = 261  # 0x0105
    RXACDIFF_D1 = 262  # 0x0106
    DC_NOTCH_1 = 263  # 0x0107
    DC_NOTCH_2 = 264  # 0x0108
    DC_NOTCH_OUT = 265  # 0x0109
    DC_NOTCH_SCALED = 266  # 0x010A
    V_FEED_IN = 267  # 0x010B
    I_TAR = 268  # 0x010C
    CONST_VLIM = 269  # 0x010D
    UNITY = 270  # 0x010E
    TXACNOTCH_1 = 271  # 0x010F
    TXACNOTCH_2 = 272  # 0x0110
    TXACNOTCH_OUT = 273  # 0x0111
    ZSYNTH_1 = 274  # 0x0112
    ZSYNTH_2 = 275  # 0x0113
    ZSYNTH_OUT_1 = 276  # 0x0114
    TXACD2_1_0 = 277  # 0x0115
    TXACD2_1_1 = 278  # 0x0116
    TXACD2_1_2 = 279  # 0x0117
    TXACD2_1_3 = 280  # 0x0118
    TXACD2_1_4 = 281  # 0x0119
    TXACD2_1_5 = 282  # 0x011A
    TXACD2_1_OUT = 283  # 0x011B
    TXACD2_2_0 = 284  # 0x011C
    TXACD2_2_1 = 285  # 0x011D
    TXACD2_2_2 = 286  # 0x011E
    TXACD2_2_3 = 287  # 0x011F
    TXACD2_2_4 = 288  # 0x0120
    TXACD2_2_5 = 289  # 0x0121
    TXACD2_2_OUT = 290  # 0x0122
    TXACD2_3_0 = 291  # 0x0123
    TXACD2_3_1 = 292  # 0x0124
    TXACD2_3_2 = 293  # 0x0125
    TXACD2_3_3 = 294  # 0x0126
    TXACD2_3_4 = 295  # 0x0127
    TXACD2_3_5 = 296  # 0x0128
    TXACD2_3_OUT = 297  # 0x0129
    RXACI2_1_1 = 298  # 0x012A
    RXACI2_1_2 = 299  # 0x012B
    RXACI2_1_3 = 300  # 0x012C
    RXACI2_1_4 = 301  # 0x012D
    RXACI2_1_OUT = 302  # 0x012E
    RXACI2_2_1 = 303  # 0x012F
    RXACI2_2_2 = 304  # 0x0130
    RXACI2_2_3 = 305  # 0x0131
    RXACI2_2_4 = 306  # 0x0132
    RXACI2_2_OUT = 307  # 0x0133
    RXACI2_3_1 = 308  # 0x0134
    RXACI2_3_2 = 309  # 0x0135
    RXACI2_3_3 = 310  # 0x0136
    RXACI2_3_4 = 311  # 0x0137
    RXACI2_3_OUT = 312  # 0x0138
    TXACCOMP1 = 313  # 0x0139
    TXACCOMP_OUT = 314  # 0x013A
    RXACCOMP1 = 315  # 0x013B
    RXACCOMP_OUT = 316  # 0x013C
    RXACHPF_D1_2 = 317  # 0x013D
    RXACHPF_D2_1 = 318  # 0x013E
    RXACHPF_D2_2 = 319  # 0x013F
    RXACHPF_OUT = 320  # 0x0140
    RXACHPF_OUT_1 = 321  # 0x0141
    RXACHPF_OUT_2 = 322  # 0x0142
    RXACEQ_OUT = 323  # 0x0143
    METER_I_1 = 324  # 0x0144
    METER_I_OUT = 325  # 0x0145
    METER_LPF_1 = 326  # 0x0146
    METER_LPF_2 = 327  # 0x0147
    METER_LPF_OUT = 328  # 0x0148
    METER_BP_1 = 329  # 0x0149
    METER_BP_2 = 330  # 0x014A
    METER_BP_OUT = 331  # 0x014B
    METER_SRC_OUT = 332  # 0x014C
    UNUSED333 = 333  # 0x014D
    UNUSED334 = 334  # 0x014E
    RING_LPF_1 = 335  # 0x014F
    RING_LPF_2 = 336  # 0x0150
    RING_LPF_OUT = 337  # 0x0151
    RING_INTERP_DIFF = 338  # 0x0152
    RING_INTERP_DIFF_OUT = 339  # 0x0153
    RING_INTERP_INT = 340  # 0x0154
    RING_INTERP_INT_OUT = 341  # 0x0155
    V_ILIM_TRACK = 342  # 0x0156
    V_RFEED_TRACK = 343  # 0x0157
    LF_SPEEDUP_CNT = 344  # 0x0158
    DC_SPEEDUP_CNT = 345  # 0x0159
    AC_SPEEDUP_CNT = 346  # 0x015A
    LCR_SPEEDUP_CNT = 347  # 0x015B
    CM_SPEEDUP_CNT = 348  # 0x015C
    DC_SPEEDUP_MASK = 349  # 0x015D
    ZSYNTH_IN = 350  # 0x015E
    I_TAR_SAVE = 351  # 0x015F
    UNUSED352 = 352  # 0x0160
    UNUSED353 = 353  # 0x0161
    COUNTER_VTR = 354  # 0x0162
    I_RING_AVG = 355  # 0x0163
    COUNTER_IRING = 356  # 0x0164
    COMP_RATIO = 357  # 0x0165
    MADC_VBAT_DIV2 = 358  # 0x0166
    VDIFF_PK_T = 359  # 0x0167
    PEAK_CNT = 360  # 0x0168
    CM_DBI_CNT = 361  # 0x0169
    VCM_LAST = 362  # 0x016A
    VBATL_SENSE = 363  # 0x016B
    VBATH_SENSE = 364  # 0x016C
    VBATR_SENSE = 365  # 0x016D
    BAT_SETTLE_CNT = 366  # 0x016E
    VBAT_TGT = 367  # 0x016F
    VBAT_REQ = 368  # 0x0170
    VCM_HIRES = 369  # 0x0171
    VCM_LORES = 370  # 0x0172
    ILOOP1 = 371  # 0x0173
    ILONG2 = 372  # 0x0174
    ITIP1 = 373  # 0x0175
    IRING1 = 374  # 0x0176
    CAL_TEMP1 = 375  # 0x0177
    CAL_TEMP2 = 376  # 0x0178
    CAL_TEMP3 = 377  # 0x0179
    CAL_TEMP4 = 378  # 0x017A
    CAL_TEMP5 = 379  # 0x017B
    CAL_TEMP6 = 380  # 0x017C
    CAL_TEMP7 = 381  # 0x017D
    CMRR_DIVISOR = 382  # 0x017E
    CMRR_REMAINDER = 383  # 0x017F
    CMRR_Q_PTR = 384  # 0x0180
    I_SOURCE1 = 385  # 0x0181
    I_SOURCE2 = 386  # 0x0182
    VTR1 = 387  # 0x0183
    VTR2 = 388  # 0x0184
    STOP_TIMER1 = 389  # 0x0185
    STOP_TIMER2 = 390  # 0x0186
    UNUSED391 = 391  # 0x0187
    UNUSED392 = 392  # 0x0188
    CAL_ONHK_Z = 393  # 0x0189
    CAL_LB_SETTLE = 394  # 0x018A
    CAL_DECLPF_V0 = 395  # 0x018B
    CAL_DECLPF_V1 = 396  # 0x018C
    CAL_DECLPF_V2 = 397  # 0x018D
    CAL_GOERTZEL_V0 = 398  # 0x018E
    CAL_GOERTZEL_V1 = 399  # 0x018F
    CAL_DECLPF_Y = 400  # 0x0190
    CAL_GOERTZEL_Y = 401  # 0x0191
    P_HVIC = 402  # 0x0192
    VBATL_MIRROR = 403  # 0x0193
    VBATH_MIRROR = 404  # 0x0194
    VBATR_MIRROR = 405  # 0x0195
    DIAG_EX1_OUT = 406  # 0x0196
    DIAG_EX2_OUT = 407  # 0x0197
    DIAG_DMM_V_OUT = 408  # 0x0198
    DIAG_DMM_I_OUT = 409  # 0x0199
    DIAG_P = 410  # 0x019A
    DIAG_LPF_V = 411  # 0x019B
    DIAG_LPF_I = 412  # 0x019C
    DIAG_TONE_FLAG = 413  # 0x019D
    ILOOP1_LAST = 414  # 0x019E
    RING_ENTRY_VOC = 415  # 0x019F
    UNUSED416 = 416  # 0x01A0
    OSC1_X_SAVE = 417  # 0x01A1
    EZSYNTH_1 = 418  # 0x01A2
    EZSYNTH_2 = 419  # 0x01A3
    ZSYNTH_OUT = 420  # 0x01A4
    UNUSED421 = 421  # 0x01A5
    CAL_SUBSTATE = 422  # 0x01A6
    DIAG_EX1_DC_OUT = 423  # 0x01A7
    DIAG_EX1_DC = 424  # 0x01A8
    EZSYNTH_B1 = 425  # 0x01A9
    EZSYNTH_B2 = 426  # 0x01AA
    EZSYNTH_A1 = 427  # 0x01AB
    EZSYNTH_A2 = 428  # 0x01AC
    ILOOP1_FILT = 429  # 0x01AD
    AC_PU_DELTA1_CNT = 430  # 0x01AE
    AC_PU_DELTA2_CNT = 431  # 0x01AF
    UNUSED432 = 432  # 0x01B0
    UNUSED433 = 433  # 0x01B1
    UNUSED434 = 434  # 0x01B2
    AC_DAC_GAIN_SAVE = 435  # 0x01B3
    RING_FLUSH_CNT = 436  # 0x01B4
    UNUSED437 = 437  # 0x01B5
    DIAG_VAR_OUT = 438  # 0x01B6
    I_VBAT = 439  # 0x01B7
    UNUSED440 = 440  # 0x01B8
    CALTMP_LOOPCNT = 441  # 0x01B9
    CALTMP_LOOPINC = 442  # 0x01BA
    UNUSED443 = 443  # 0x01BB
    CALTMP_CODEINC = 444  # 0x01BC
    CALTMP_TAUINC = 445  # 0x01BD
    CALTMP_TAU = 446  # 0x01BE
    CAL_TEMP8 = 447  # 0x01BF
    PATCHID = 448  # 0x01C0
    UNUSED449 = 449  # 0x01C1
    UNUSED450 = 450  # 0x01C2
    UNUSED451 = 451  # 0x01C3
    CAL_LB_OFFSET_FWD = 452  # 0x01C4
    CAL_LB_OFFSET_RVS = 453  # 0x01C5
    COUNT_SPEEDUP = 454  # 0x01C6
    SWEEP_COUNT = 455  # 0x01C7
    AMP_RAMP = 456  # 0x01C8
    DIAG_LPF_MADC_D = 457  # 0x01C9
    DIAG_HPF_MADC = 458  # 0x01CA
    UNUSED459 = 459  # 0x01CB
    TXDEC_OUT = 460  # 0x01CC
    TXDEC_D1 = 461  # 0x01CD
    TXDEC_D2 = 462  # 0x01CE
    RXDEC_D1 = 463  # 0x01CF
    RXDEC_D2 = 464  # 0x01D0
    OSCINT1_D2_1 = 465  # 0x01D1
    OSCINT1_D1_1 = 466  # 0x01D2
    OSCINT1_OUT_1 = 467  # 0x01D3
    OSCINT1_D2_2 = 468  # 0x01D4
    OSCINT1_D1_2 = 469  # 0x01D5
    OSCINT1_OUT = 470  # 0x01D6
    OSCINT2_D2_1 = 471  # 0x01D7
    OSCINT2_D1_1 = 472  # 0x01D8
    OSCINT2_OUT_1 = 473  # 0x01D9
    OSCINT2_D2_2 = 474  # 0x01DA
    OSCINT2_D1_2 = 475  # 0x01DB
    OSCINT2_OUT = 476  # 0x01DC
    OSC1_Y_SAVE = 477  # 0x01DD
    OSC2_Y_SAVE = 478  # 0x01DE
    PWRSAVE_CNT = 479  # 0x01DF
    VBATR_PK = 480  # 0x01E0
    SPEEDUP_MASK_CNT = 481  # 0x01E1
    VCM_RING_FIXED = 482  # 0x01E2
    DELTA_VCM = 483  # 0x01E3
    MADC_VTIPC_DIAG_OS = 484  # 0x01E4
    MADC_VRINGC_DIAG_OS = 485  # 0x01E5
    MADC_VLONG_DIAG_OS = 486  # 0x01E6
    UNUSED487 = 487  # 0x01E7
    UNUSED488 = 488  # 0x01E8
    UNUSED489 = 489  # 0x01E9
    UNUSED490 = 490  # 0x01EA
    UNUSED491 = 491  # 0x01EB
    PWRSAVE_DBI_CNT = 492  # 0x01EC
    COMP_RATIO_SAVE = 493  # 0x01ED
    CAL_TEMP9 = 494  # 0x01EE
    CAL_TEMP10 = 495  # 0x01EF
    DAC_OFFSET_TEMP = 496  # 0x01F0
    CAL_DAC_CODE = 497  # 0x01F1
    DCDAC_OFFSET = 498  # 0x01F2
    VDIFF_COARSE = 499  # 0x01F3
    RXACIIR_OUT_4 = 500  # 0x01F4
    CAL_TEMP11 = 501  # 0x01F5
    METER_RAMP = 502  # 0x01F6
    METER_RAMP_DIR = 503  # 0x01F7
    METER_ON_T = 504  # 0x01F8
    METER_PK_DET = 505  # 0x01F9
    METER_PK_DET_T = 506  # 0x01FA
    THERM_CNT = 507  # 0x01FB
    VDIFF_SENSE_DELAY = 508  # 0x01FC
    RING_INTERP_DIFF_SYNC = 509  # 0x01FD
    CPUMP_DEB_CNT = 510  # 0x01FE
    UNUSED511 = 511  # 0x01FF
    MINUS_ONE = 512  # 0x0200
    ILOOPLPF = 513  # 0x0201
    ILONGLPF = 514  # 0x0202
    BATLPF = 515  # 0x0203
    VDIFFLPF = 516  # 0x0204
    VCMLPF = 517  # 0x0205
    TXACIIR_B0_1 = 518  # 0x0206
    TXACIIR_B1_1 = 519  # 0x0207
    TXACIIR_A1_1 = 520  # 0x0208
    TXACIIR_B0_2 = 521  # 0x0209
    TXACIIR_B1_2 = 522  # 0x020A
    TXACIIR_B2_2 = 523  # 0x020B
    TXACIIR_A1_2 = 524  # 0x020C
    TXACIIR_A2_2 = 525  # 0x020D
    TXACIIR_B0_3 = 526  # 0x020E
    TXACIIR_B1_3 = 527  # 0x020F
    TXACIIR_B2_3 = 528  # 0x0210
    TXACIIR_A1_3 = 529  # 0x0211
    TXACIIR_A2_3 = 530  # 0x0212
    TXACHPF_B0_1 = 531  # 0x0213
    TXACHPF_B1_1 = 532  # 0x0214
    TXACHPF_A1_1 = 533  # 0x0215
    TXACHPF_B0_2 = 534  # 0x0216
    TXACHPF_B1_2 = 535  # 0x0217
    TXACHPF_B2_2 = 536  # 0x0218
    TXACHPF_A1_2 = 537  # 0x0219
    TXACHPF_A2_2 = 538  # 0x021A
    TXACHPF_GAIN = 539  # 0x021B
    TXACEQ_C0 = 540  # 0x021C
    TXACEQ_C1 = 541  # 0x021D
    TXACEQ_C2 = 542  # 0x021E
    TXACEQ_C3 = 543  # 0x021F
    TXACGAIN = 544  # 0x0220
    RXACGAIN = 545  # 0x0221
    RXACEQ_C0 = 546  # 0x0222
    RXACEQ_C1 = 547  # 0x0223
    RXACEQ_C2 = 548  # 0x0224
    RXACEQ_C3 = 549  # 0x0225
    RXACIIR_B0_1 = 550  # 0x0226
    RXACIIR_B1_1 = 551  # 0x0227
    RXACIIR_A1_1 = 552  # 0x0228
    RXACIIR_B0_2 = 553  # 0x0229
    RXACIIR_B1_2 = 554  # 0x022A
    RXACIIR_B2_2 = 555  # 0x022B
    RXACIIR_A1_2 = 556  # 0x022C
    RXACIIR_A2_2 = 557  # 0x022D
    RXACIIR_B0_3 = 558  # 0x022E
    RXACIIR_B1_3 = 559  # 0x022F
    RXACIIR_B2_3 = 560  # 0x0230
    RXACIIR_A1_3 = 561  # 0x0231
    RXACIIR_A2_3 = 562  # 0x0232
    ECFIR_C2 = 563  # 0x0233
    ECFIR_C3 = 564  # 0x0234
    ECFIR_C4 = 565  # 0x0235
    ECFIR_C5 = 566  # 0x0236
    ECFIR_C6 = 567  # 0x0237
    ECFIR_C7 = 568  # 0x0238
    ECFIR_C8 = 569  # 0x0239
    ECFIR_C9 = 570  # 0x023A
    ECIIR_B0 = 571  # 0x023B
    ECIIR_B1 = 572  # 0x023C
    ECIIR_A1 = 573  # 0x023D
    ECIIR_A2 = 574  # 0x023E
    DTMFDTF_B0_1 = 575  # 0x023F
    DTMFDTF_B1_1 = 576  # 0x0240
    DTMFDTF_B2_1 = 577  # 0x0241
    DTMFDTF_A1_1 = 578  # 0x0242
    DTMFDTF_A2_1 = 579  # 0x0243
    DTMFDTF_B0_2 = 580  # 0x0244
    DTMFDTF_B1_2 = 581  # 0x0245
    DTMFDTF_B2_2 = 582  # 0x0246
    DTMFDTF_A1_2 = 583  # 0x0247
    DTMFDTF_A2_2 = 584  # 0x0248
    DTMFDTF_B0_3 = 585  # 0x0249
    DTMFDTF_B1_3 = 586  # 0x024A
    DTMFDTF_B2_3 = 587  # 0x024B
    DTMFDTF_A1_3 = 588  # 0x024C
    DTMFDTF_A2_3 = 589  # 0x024D
    DTMFDTF_GAIN = 590  # 0x024E
    DTMFLPF_B0_1 = 591  # 0x024F
    DTMFLPF_B1_1 = 592  # 0x0250
    DTMFLPF_B2_1 = 593  # 0x0251
    DTMFLPF_A1_1 = 594  # 0x0252
    DTMFLPF_A2_1 = 595  # 0x0253
    DTMFLPF_B0_2 = 596  # 0x0254
    DTMFLPF_B1_2 = 597  # 0x0255
    DTMFLPF_B2_2 = 598  # 0x0256
    DTMFLPF_A1_2 = 599  # 0x0257
    DTMFLPF_A2_2 = 600  # 0x0258
    DTMFLPF_GAIN = 601  # 0x0259
    DTMFHPF_B0_1 = 602  # 0x025A
    DTMFHPF_B1_1 = 603  # 0x025B
    DTMFHPF_B2_1 = 604  # 0x025C
    DTMFHPF_A1_1 = 605  # 0x025D
    DTMFHPF_A2_1 = 606  # 0x025E
    DTMFHPF_B0_2 = 607  # 0x025F
    DTMFHPF_B1_2 = 608  # 0x0260
    DTMFHPF_B2_2 = 609  # 0x0261
    DTMFHPF_A1_2 = 610  # 0x0262
    DTMFHPF_A2_2 = 611  # 0x0263
    DTMFHPF_GAIN = 612  # 0x0264
    POWER_GAIN = 613  # 0x0265
    GOERTZEL_GAIN = 614  # 0x0266
    MODEM_GAIN = 615  # 0x0267
    HOTBIT1 = 616  # 0x0268
    HOTBIT0 = 617  # 0x0269
    ROW0_C1 = 618  # 0x026A
    ROW1_C1 = 619  # 0x026B
    ROW2_C1 = 620  # 0x026C
    ROW3_C1 = 621  # 0x026D
    COL0_C1 = 622  # 0x026E
    COL1_C1 = 623  # 0x026F
    COL2_C1 = 624  # 0x0270
    COL3_C1 = 625  # 0x0271
    ROW0_C2 = 626  # 0x0272
    ROW1_C2 = 627  # 0x0273
    ROW2_C2 = 628  # 0x0274
    ROW3_C2 = 629  # 0x0275
    COL0_C2 = 630  # 0x0276
    COL1_C2 = 631  # 0x0277
    COL2_C2 = 632  # 0x0278
    COL3_C2 = 633  # 0x0279
    SLOPE_VLIM = 634  # 0x027A
    SLOPE_RFEED = 635  # 0x027B
    SLOPE_ILIM = 636  # 0x027C
    SLOPE_RING = 637  # 0x027D
    SLOPE_DELTA1 = 638  # 0x027E
    SLOPE_DELTA2 = 639  # 0x027F
    V_VLIM = 640  # 0x0280
    V_RFEED = 641  # 0x0281
    V_ILIM = 642  # 0x0282
    CONST_RFEED = 643  # 0x0283
    CONST_ILIM = 644  # 0x0284
    I_VLIM = 645  # 0x0285
    DC_DAC_GAIN = 646  # 0x0286
    VDIFF_TH = 647  # 0x0287
    TXDEC_B0 = 648  # 0x0288
    TXDEC_B1 = 649  # 0x0289
    TXDEC_B2 = 650  # 0x028A
    TXDEC_A1 = 651  # 0x028B
    TXDEC_A2 = 652  # 0x028C
    ZSYNTH_B0 = 653  # 0x028D
    ZSYNTH_B1 = 654  # 0x028E
    ZSYNTH_B2 = 655  # 0x028F
    ZSYNTH_A1 = 656  # 0x0290
    ZSYNTH_A2 = 657  # 0x0291
    RXACHPF_B0_1 = 658  # 0x0292
    RXACHPF_B1_1 = 659  # 0x0293
    RXACHPF_A1_1 = 660  # 0x0294
    RXACHPF_B0_2 = 661  # 0x0295
    RXACHPF_B1_2 = 662  # 0x0296
    RXACHPF_B2_2 = 663  # 0x0297
    RXACHPF_A1_2 = 664  # 0x0298
    RXACHPF_A2_2 = 665  # 0x0299
    RXACHPF_GAIN = 666  # 0x029A
    MASK7LSB = 667  # 0x029B
    RXDEC_B0 = 668  # 0x029C
    RXDEC_B1 = 669  # 0x029D
    RXDEC_B2 = 670  # 0x029E
    RXDEC_A1 = 671  # 0x029F
    RXDEC_A2 = 672  # 0x02A0
    OSCINT1_B0_1 = 673  # 0x02A1
    OSCINT1_B1_1 = 674  # 0x02A2
    OSCINT1_B2_1 = 675  # 0x02A3
    OSCINT1_A1_1 = 676  # 0x02A4
    OSCINT1_A2_1 = 677  # 0x02A5
    OSCINT1_B0_2 = 678  # 0x02A6
    OSCINT1_B1_2 = 679  # 0x02A7
    OSCINT1_B2_2 = 680  # 0x02A8
    OSCINT1_A1_2 = 681  # 0x02A9
    OSCINT1_A2_2 = 682  # 0x02AA
    OSCINT2_B0_1 = 683  # 0x02AB
    OSCINT2_B1_1 = 684  # 0x02AC
    OSCINT2_B2_1 = 685  # 0x02AD
    OSCINT2_A1_1 = 686  # 0x02AE
    OSCINT2_A2_1 = 687  # 0x02AF
    OSCINT2_B0_2 = 688  # 0x02B0
    OSCINT2_B1_2 = 689  # 0x02B1
    OSCINT2_B2_2 = 690  # 0x02B2
    OSCINT2_A1_2 = 691  # 0x02B3
    OSCINT2_A2_2 = 692  # 0x02B4
    UNUSED693 = 693  # 0x02B5
    UNUSED694 = 694  # 0x02B6
    UNUSED695 = 695  # 0x02B7
    RING_LPF_B0 = 696  # 0x02B8
    RING_LPF_B1 = 697  # 0x02B9
    RING_LPF_B2 = 698  # 0x02BA
    RING_LPF_A1 = 699  # 0x02BB
    RING_LPF_A2 = 700  # 0x02BC
    LCRDBI = 701  # 0x02BD
    LONGDBI = 702  # 0x02BE
    VBAT_TIMER = 703  # 0x02BF
    LF_SPEEDUP_TIMER = 704  # 0x02C0
    DC_SPEEDUP_TIMER = 705  # 0x02C1
    AC_SPEEDUP_TIMER = 706  # 0x02C2
    LCR_SPEEDUP_TIMER = 707  # 0x02C3
    CM_SPEEDUP_TIMER = 708  # 0x02C4
    VCM_TH = 709  # 0x02C5
    AC_SPEEDUP_TH = 710  # 0x02C6
    SPR_SIG_0 = 711  # 0x02C7
    SPR_SIG_1 = 712  # 0x02C8
    SPR_SIG_2 = 713  # 0x02C9
    SPR_SIG_3 = 714  # 0x02CA
    SPR_SIG_4 = 715  # 0x02CB
    SPR_SIG_5 = 716  # 0x02CC
    SPR_SIG_6 = 717  # 0x02CD
    SPR_SIG_7 = 718  # 0x02CE
    SPR_SIG_8 = 719  # 0x02CF
    SPR_SIG_9 = 720  # 0x02D0
    SPR_SIG_10 = 721  # 0x02D1
    SPR_SIG_11 = 722  # 0x02D2
    SPR_SIG_12 = 723  # 0x02D3
    SPR_SIG_13 = 724  # 0x02D4
    SPR_SIG_14 = 725  # 0x02D5
    SPR_SIG_15 = 726  # 0x02D6
    SPR_SIG_16 = 727  # 0x02D7
    SPR_SIG_17 = 728  # 0x02D8
    SPR_SIG_18 = 729  # 0x02D9
    COUNTER_VTR_VAL = 730  # 0x02DA
    CONST_028 = 731  # 0x02DB
    CONST_032 = 732  # 0x02DC
    CONST_038 = 733  # 0x02DD
    CONST_046 = 734  # 0x02DE
    COUNTER_IRING_VAL = 735  # 0x02DF
    GAIN_RING = 736  # 0x02E0
    RING_HYST = 737  # 0x02E1
    COMP_Z = 738  # 0x02E2
    CONST_115 = 739  # 0x02E3
    CONST_110 = 740  # 0x02E4
    CONST_105 = 741  # 0x02E5
    CONST_100 = 742  # 0x02E6
    CONST_095 = 743  # 0x02E7
    CONST_090 = 744  # 0x02E8
    CONST_085 = 745  # 0x02E9
    V_RASUM_IDEAL = 746  # 0x02EA
    CONST_ONE = 747  # 0x02EB
    VCM_OH = 748  # 0x02EC
    VCM_RING = 749  # 0x02ED
    VCM_HYST = 750  # 0x02EE
    VOV_GND = 751  # 0x02EF
    VOV_BAT = 752  # 0x02F0
    VOV_RING_BAT = 753  # 0x02F1
    CM_DBI = 754  # 0x02F2
    RTPER = 755  # 0x02F3
    P_TH_HVIC = 756  # 0x02F4
    UNUSED757 = 757  # 0x02F5
    UNUSED758 = 758  # 0x02F6
    COEF_P_HVIC = 759  # 0x02F7
    UNUSED760 = 760  # 0x02F8
    UNUSED761 = 761  # 0x02F9
    UNUSED762 = 762  # 0x02FA
    UNUSED763 = 763  # 0x02FB
    BAT_HYST = 764  # 0x02FC
    BAT_DBI = 765  # 0x02FD
    VBATL_EXPECT = 766  # 0x02FE
    VBATH_EXPECT = 767  # 0x02FF
    VBATR_EXPECT = 768  # 0x0300
    BAT_SETTLE = 769  # 0x0301
    VBAT_IRQ_TH = 770  # 0x0302
    MADC_VTIPC_OS = 771  # 0x0303
    MADC_VRINGC_OS = 772  # 0x0304
    MADC_VBAT_OS = 773  # 0x0305
    MADC_VLONG_OS = 774  # 0x0306
    UNUSED775 = 775  # 0x0307
    MADC_VDC_OS = 776  # 0x0308
    MADC_ILONG_OS = 777  # 0x0309
    UNUSED778 = 778  # 0x030A
    UNUSED779 = 779  # 0x030B
    MADC_ILOOP_OS = 780  # 0x030C
    MADC_ILOOP_SCALE = 781  # 0x030D
    UNUSED782 = 782  # 0x030E
    UNUSED783 = 783  # 0x030F
    DC_ADC_OS = 784  # 0x0310
    CAL_UNITY = 785  # 0x0311
    UNUSED786 = 786  # 0x0312
    UNUSED787 = 787  # 0x0313
    ACADC_OFFSET = 788  # 0x0314
    ACDAC_OFFSET = 789  # 0x0315
    CAL_DCDAC_CODE = 790  # 0x0316
    CAL_DCDAC_15MA = 791  # 0x0317
    UNUSED792 = 792  # 0x0318
    UNUSED793 = 793  # 0x0319
    UNUSED794 = 794  # 0x031A
    UNUSED795 = 795  # 0x031B
    UNUSED796 = 796  # 0x031C
    UNUSED797 = 797  # 0x031D
    UNUSED798 = 798  # 0x031E
    UNUSED799 = 799  # 0x031F
    UNUSED800 = 800  # 0x0320
    CAL_LB_TSQUELCH = 801  # 0x0321
    CAL_LB_TCHARGE = 802  # 0x0322
    CAL_LB_TSETTLE0 = 803  # 0x0323
    CAL_GOERTZEL_DLY = 804  # 0x0324
    CAL_GOERTZEL_ALPHA = 805  # 0x0325
    CAL_DECLPF_K = 806  # 0x0326
    CAL_DECLPF_B1 = 807  # 0x0327
    CAL_DECLPF_B2 = 808  # 0x0328
    CAL_DECLPF_A1 = 809  # 0x0329
    CAL_DECLPF_A2 = 810  # 0x032A
    CAL_ACADC_THRL = 811  # 0x032B
    CAL_ACADC_THRH = 812  # 0x032C
    CAL_ACADC_TSETTLE = 813  # 0x032D
    DTROW0TH = 814  # 0x032E
    DTROW1TH = 815  # 0x032F
    DTROW2TH = 816  # 0x0330
    DTROW3TH = 817  # 0x0331
    DTCOL0TH = 818  # 0x0332
    DTCOL1TH = 819  # 0x0333
    DTCOL2TH = 820  # 0x0334
    DTCOL3TH = 821  # 0x0335
    DTFTWTH = 822  # 0x0336
    DTRTWTH = 823  # 0x0337
    DTROWRTH = 824  # 0x0338
    DTCOLRTH = 825  # 0x0339
    DTROW2HTH = 826  # 0x033A
    DTCOL2HTH = 827  # 0x033B
    DTMINPTH = 828  # 0x033C
    DTHOTTH = 829  # 0x033D
    RXPWR = 830  # 0x033E
    TXPWR = 831  # 0x033F
    RXMODPWR = 832  # 0x0340
    TXMODPWR = 833  # 0x0341
    FSKFREQ0 = 834  # 0x0342
    FSKFREQ1 = 835  # 0x0343
    FSKAMP0 = 836  # 0x0344
    FSKAMP1 = 837  # 0x0345
    FSK01 = 838  # 0x0346
    FSK10 = 839  # 0x0347
    VOCDELTA = 840  # 0x0348
    VOCLTH = 841  # 0x0349
    VOCHTH = 842  # 0x034A
    RINGOF = 843  # 0x034B
    RINGFR = 844  # 0x034C
    RINGAMP = 845  # 0x034D
    RINGPHAS = 846  # 0x034E
    RTDCTH = 847  # 0x034F
    RTACTH = 848  # 0x0350
    RTDCDB = 849  # 0x0351
    RTACDB = 850  # 0x0352
    RTCOUNT = 851  # 0x0353
    LCROFFHK = 852  # 0x0354
    LCRONHK = 853  # 0x0355
    LCRMASK = 854  # 0x0356
    LCRMASK_POLREV = 855  # 0x0357
    LCRMASK_STATE = 856  # 0x0358
    LCRMASK_LINECAP = 857  # 0x0359
    LONGHITH = 858  # 0x035A
    LONGLOTH = 859  # 0x035B
    IRING_LIM = 860  # 0x035C
    AC_PU_DELTA1 = 861  # 0x035D
    AC_PU_DELTA2 = 862  # 0x035E
    DIAG_LPF_8K = 863  # 0x035F
    DIAG_LPF_128K = 864  # 0x0360
    DIAG_INV_N = 865  # 0x0361
    DIAG_GAIN = 866  # 0x0362
    DIAG_G_CAL = 867  # 0x0363
    DIAG_OS_CAL = 868  # 0x0364
    SPR_GAIN_TRIM = 869  # 0x0365
    UNUSED870 = 870  # 0x0366
    AC_DAC_GAIN = 871  # 0x0367
    UNUSED872 = 872  # 0x0368
    UNUSED873 = 873  # 0x0369
    AC_DAC_GAIN0 = 874  # 0x036A
    EZSYNTH_B0 = 875  # 0x036B
    UNUSED876 = 876  # 0x036C
    UNUSED877 = 877  # 0x036D
    UNUSED878 = 878  # 0x036E
    UNUSED879 = 879  # 0x036F
    AC_ADC_GAIN = 880  # 0x0370
    ILOOP1LPF = 881  # 0x0371
    RING_FLUSH_TIMER = 882  # 0x0372
    ALAW_BIAS = 883  # 0x0373
    MADC_VTRC_SCALE = 884  # 0x0374
    UNUSED885 = 885  # 0x0375
    MADC_VBAT_SCALE = 886  # 0x0376
    MADC_VLONG_SCALE = 887  # 0x0377
    MADC_VLONG_SCALE_RING = 888  # 0x0378
    UNUSED889 = 889  # 0x0379
    MADC_VDC_SCALE = 890  # 0x037A
    MADC_ILONG_SCALE = 891  # 0x037B
    UNUSED892 = 892  # 0x037C
    UNUSED893 = 893  # 0x037D
    VDIFF_SENSE_SCALE = 894  # 0x037E
    VDIFF_SENSE_SCALE_RING = 895  # 0x037F
    VOV_RING_GND = 896  # 0x0380
    DIAG_GAIN_DC = 897  # 0x0381
    CAL_LB_OSC1_FREQ = 898  # 0x0382
    CAL_DCDAC_9TAU = 899  # 0x0383
    CAL_MADC_9TAU = 900  # 0x0384
    ADAP_RING_MIN_I = 901  # 0x0385
    SWEEP_STEP = 902  # 0x0386
    SWEEP_STEP_SAVE = 903  # 0x0387
    SWEEP_REF = 904  # 0x0388
    AMP_STEP = 905  # 0x0389
    RXACGAIN_SAVE = 906  # 0x038A
    AMP_RAMP_INIT = 907  # 0x038B
    DIAG_HPF_GAIN = 908  # 0x038C
    DIAG_HPF_8K = 909  # 0x038D
    DIAG_ADJ_STEP = 910  # 0x038E
    UNUSED911 = 911  # 0x038F
    UNUSED912 = 912  # 0x0390
    MADC_SCALE_INV = 913  # 0x0391
    UNUSED914 = 914  # 0x0392
    PWRSAVE_TIMER = 915  # 0x0393
    OFFHOOK_THRESH = 916  # 0x0394
    SPEEDUP_MASK_TIMER = 917  # 0x0395
    UNUSED918 = 918  # 0x0396
    VBAT_TRACK_MIN = 919  # 0x0397
    VBAT_TRACK_MIN_RNG = 920  # 0x0398
    UNUSED921 = 921  # 0x0399
    UNUSED922 = 922  # 0x039A
    UNUSED923 = 923  # 0x039B
    UNUSED924 = 924  # 0x039C
    UNUSED925 = 925  # 0x039D
    UNUSED926 = 926  # 0x039E
    DC_HOLD_DAC_OS = 927  # 0x039F
    UNUSED928 = 928  # 0x03A0
    NOTCH_B0 = 929  # 0x03A1
    NOTCH_B1 = 930  # 0x03A2
    NOTCH_B2 = 931  # 0x03A3
    NOTCH_A1 = 932  # 0x03A4
    NOTCH_A2 = 933  # 0x03A5
    METER_LPF_B0 = 934  # 0x03A6
    METER_LPF_B1 = 935  # 0x03A7
    METER_LPF_B2 = 936  # 0x03A8
    METER_LPF_A1 = 937  # 0x03A9
    METER_LPF_A2 = 938  # 0x03AA
    METER_SIG_0 = 939  # 0x03AB
    METER_SIG_1 = 940  # 0x03AC
    METER_SIG_2 = 941  # 0x03AD
    METER_SIG_3 = 942  # 0x03AE
    METER_SIG_4 = 943  # 0x03AF
    METER_SIG_5 = 944  # 0x03B0
    METER_SIG_6 = 945  # 0x03B1
    METER_SIG_7 = 946  # 0x03B2
    METER_SIG_8 = 947  # 0x03B3
    METER_SIG_9 = 948  # 0x03B4
    METER_SIG_10 = 949  # 0x03B5
    METER_SIG_11 = 950  # 0x03B6
    METER_SIG_12 = 951  # 0x03B7
    METER_SIG_13 = 952  # 0x03B8
    METER_SIG_14 = 953  # 0x03B9
    METER_SIG_15 = 954  # 0x03BA
    METER_BP_B0 = 955  # 0x03BB
    METER_BP_B1 = 956  # 0x03BC
    METER_BP_B2 = 957  # 0x03BD
    METER_BP_A1 = 958  # 0x03BE
    METER_BP_A2 = 959  # 0x03BF
    PM_AMP_THRESH = 960  # 0x03C0
    METER_GAIN = 961  # 0x03C1
    PWRSAVE_DBI = 962  # 0x03C2
    DCDC_ANA_SCALE = 963  # 0x03C3
    VOV_BAT_PWRSAVE_LO = 964  # 0x03C4
    VOV_BAT_PWRSAVE_HI = 965  # 0x03C5
    AC_ADC_GAIN0 = 966  # 0x03C6
    SCALE_KAUDIO = 967  # 0x03C7
    METER_GAIN_TEMP = 968  # 0x03C8
    METER_RAMP_STEP = 969  # 0x03C9
    THERM_DBI = 970  # 0x03CA
    LPR_SCALE = 971  # 0x03CB
    LPR_CM_OS = 972  # 0x03CC
    VOV_DCDC_SLOPE = 973  # 0x03CD
    VOV_DCDC_OS = 974  # 0x03CE
    VOV_RING_BAT_MAX = 975  # 0x03CF
    SLOPE_VLIM1 = 976  # 0x03D0
    SLOPE_RFEED1 = 977  # 0x03D1
    SLOPE_ILIM1 = 978  # 0x03D2
    V_VLIM1 = 979  # 0x03D3
    V_RFEED1 = 980  # 0x03D4
    V_ILIM1 = 981  # 0x03D5
    CONST_RFEED1 = 982  # 0x03D6
    CONST_ILIM1 = 983  # 0x03D7
    I_VLIM1 = 984  # 0x03D8
    SLOPE_VLIM2 = 985  # 0x03D9
    SLOPE_RFEED2 = 986  # 0x03DA
    SLOPE_ILIM2 = 987  # 0x03DB
    V_VLIM2 = 988  # 0x03DC
    V_RFEED2 = 989  # 0x03DD
    V_ILIM2 = 990  # 0x03DE
    CONST_RFEED2 = 991  # 0x03DF
    CONST_ILIM2 = 992  # 0x03E0
    I_VLIM2 = 993  # 0x03E1
    DIAG_V_TAR = 994  # 0x03E2
    DIAG_V_TAR2 = 995  # 0x03E3
    STOP_TIMER1_VAL = 996  # 0x03E4
    STOP_TIMER2_VAL = 997  # 0x03E5
    DIAG_VCM1_TAR = 998  # 0x03E6
    DIAG_VCM_STEP = 999  # 0x03E7
    LKG_DNT_HIRES = 1000  # 0x03E8
    LKG_DNR_HIRES = 1001  # 0x03E9
    LINEAR_OS = 1002  # 0x03EA
    CPUMP_DEB = 1003  # 0x03EB
    DCDC_VERR = 1004  # 0x03EC
    DCDC_VERR_HYST = 1005  # 0x03ED
    DCDC_OITHRESH_LO = 1006  # 0x03EE
    DCDC_OITHRESH_HI = 1007  # 0x03EF
    HV_BIAS_ONHK = 1008  # 0x03F0
    HV_BIAS_OFFHK = 1009  # 0x03F1
    UNUSED1010 = 1010  # 0x03F2
    UNUSED1011 = 1011  # 0x03F3
    UNUSED1012 = 1012  # 0x03F4
    UNUSED1013 = 1013  # 0x03F5
    ILONG_RT_THRESH = 1014  # 0x03F6
    VOV_RING_BAT_DCDC = 1015  # 0x03F7
    UNUSED1016 = 1016  # 0x03F8
    LKG_LB_OFFSET = 1017  # 0x03F9
    LKG_OFHK_OFFSET = 1018  # 0x03FA
    SWEEP_FREQ_TH = 1019  # 0x03FB
    AMP_MOD_G = 1020  # 0x03FC
    AMP_MOD_OS = 1021  # 0x03FD
    UNUSED1022 = 1022  # 0x03FE
    UNUSED1023 = 1023  # 0x03FF
    UNUSED_REG256 = 1280  # 0x0500
    DAC_IN = 1281  # 0x0501
    ADC_OUT = 1282  # 0x0502
    PASS1 = 1283  # 0x0503
    TX_AC_INT = 1284  # 0x0504
    RX_AC_DIFF = 1285  # 0x0505
    INDIRECT_WR = 1286  # 0x0506
    INDIRECT_RD = 1287  # 0x0507
    BYPASS_OUT = 1288  # 0x0508
    ACC = 1289  # 0x0509
    INDIRECT_RAM_A = 1290  # 0x050A
    INDIRECT_RAM_B = 1291  # 0x050B
    HOT_BIT1 = 1292  # 0x050C
    HOT_BIT0 = 1293  # 0x050D
    PASS0_ROW_PWR = 1294  # 0x050E
    PASS0_COL_PWR = 1295  # 0x050F
    PASS0_ROW = 1296  # 0x0510
    PASS0_COL = 1297  # 0x0511
    PASS0_ROW_REL = 1298  # 0x0512
    PASS0_COL_REL = 1299  # 0x0513
    PASS0_ROW_2ND = 1300  # 0x0514
    PASS0_COL_2ND = 1301  # 0x0515
    PASS0_REV_TW = 1302  # 0x0516
    PASS0_FWD_TW = 1303  # 0x0517
    DAA_ADC_OUT = 1304  # 0x0518
    CAL_CM_BAL_TEST = 1305  # 0x0519
    UNUSED_REG282 = 1306  # 0x051A
    TONE1 = 1307  # 0x051B
    TONE2 = 1308  # 0x051C
    RING_TRIG = 1309  # 0x051D
    VCM_DAC = 1310  # 0x051E
    UNUSED_REG287 = 1311  # 0x051F
    RING_DAC = 1312  # 0x0520
    VRING_CROSSING = 1313  # 0x0521
    UNUSED_REG290 = 1314  # 0x0522
    LINEFEED_SHADOW = 1315  # 0x0523
    UNUSED_REG292 = 1316  # 0x0524
    UNUSED_REG293 = 1317  # 0x0525
    UNUSED_REG294 = 1318  # 0x0526
    ROW_DIGIT = 1319  # 0x0527
    COL_DIGIT = 1320  # 0x0528
    UNUSED_REG297 = 1321  # 0x0529
    PQ1_IRQ = 1322  # 0x052A
    PQ2_IRQ = 1323  # 0x052B
    PQ3_IRQ = 1324  # 0x052C
    PQ4_IRQ = 1325  # 0x052D
    PQ5_IRQ = 1326  # 0x052E
    PQ6_IRQ = 1327  # 0x052F
    LCR_SET = 1328  # 0x0530
    LCR_CLR = 1329  # 0x0531
    RTP_SET = 1330  # 0x0532
    LONG_SET = 1331  # 0x0533
    LONG_CLR = 1332  # 0x0534
    VDIFF_IRQ = 1333  # 0x0535
    MODFEED_SET = 1334  # 0x0536
    MODFEED_CLR = 1335  # 0x0537
    LF_SPEEDUP_SET = 1336  # 0x0538
    LF_SPEEDUP_CLR = 1337  # 0x0539
    DC_SPEEDUP_SET = 1338  # 0x053A
    DC_SPEEDUP_CLR = 1339  # 0x053B
    AC_SPEEDUP_SET = 1340  # 0x053C
    AC_SPEEDUP_CLR = 1341  # 0x053D
    LCR_SPEEDUP_SET = 1342  # 0x053E
    LCR_SPEEDUP_CLR = 1343  # 0x053F
    CM_SPEEDUP_SET = 1344  # 0x0540
    CM_SPEEDUP_CLR = 1345  # 0x0541
    MODEMPASS0 = 1346  # 0x0542
    RX2100_PASS1_PWR = 1347  # 0x0543
    RX2100_PASS1_THR = 1348  # 0x0544
    TX2100_PASS1_PWR = 1349  # 0x0545
    TX2100_PASS1_THR = 1350  # 0x0546
    TXMDM_TRIG = 1351  # 0x0547
    RXMDM_TRIG = 1352  # 0x0548
    UNUSED_REG329 = 1353  # 0x0549
    TX_FILT_CLR = 1354  # 0x054A
    TX_DC_INT = 1355  # 0x054B
    RX_DC_MOD_IN = 1356  # 0x054C
    DSP_ACCESS = 1357  # 0x054D
    PRAM_ADDR = 1358  # 0x054E
    PRAM_DATA = 1359  # 0x054F
    IND_RAM_A_BASE = 1360  # 0x0550
    IND_RAM_A_ADDR = 1361  # 0x0551
    IND_RAM_A_MOD = 1362  # 0x0552
    IND_RAM_B_BASE = 1363  # 0x0553
    IND_RAM_B_ADDR = 1364  # 0x0554
    IND_RAM_B_MOD = 1365  # 0x0555
    UNUSED_REG342 = 1366  # 0x0556
    UNUSED_REG343 = 1367  # 0x0557
    UNUSED_REG344 = 1368  # 0x0558
    USER_B0 = 1369  # 0x0559
    USER_B1 = 1370  # 0x055A
    USER_B2 = 1371  # 0x055B
    USER_B3 = 1372  # 0x055C
    USER_B4 = 1373  # 0x055D
    USER_B5 = 1374  # 0x055E
    USER_B6 = 1375  # 0x055F
    USER_B7 = 1376  # 0x0560
    FLUSH_AUDIO_CLR = 1377  # 0x0561
    FLUSH_DC_CLR = 1378  # 0x0562
    SPR_CLR = 1379  # 0x0563
    GPI0 = 1380  # 0x0564
    GPI1 = 1381  # 0x0565
    GPI2 = 1382  # 0x0566
    GPI3 = 1383  # 0x0567
    GPO0 = 1384  # 0x0568
    GPO1 = 1385  # 0x0569
    GPO2 = 1386  # 0x056A
    GPO3 = 1387  # 0x056B
    GPO0_OE = 1388  # 0x056C
    GPO1_OE = 1389  # 0x056D
    GPO2_OE = 1390  # 0x056E
    GPO3_OE = 1391  # 0x056F
    BATSEL_L_SET = 1392  # 0x0570
    BATSEL_H_SET = 1393  # 0x0571
    BATSEL_R_SET = 1394  # 0x0572
    BATSEL_CLR = 1395  # 0x0573
    VBAT_IRQ = 1396  # 0x0574
    MADC_VTIPC_RAW = 1397  # 0x0575
    MADC_VRINGC_RAW = 1398  # 0x0576
    MADC_VBAT_RAW = 1399  # 0x0577
    MADC_VLONG_RAW = 1400  # 0x0578
    UNUSED_REG377 = 1401  # 0x0579
    MADC_VDC_RAW = 1402  # 0x057A
    MADC_ILONG_RAW = 1403  # 0x057B
    UNUSED_REG380 = 1404  # 0x057C
    UNUSED_REG381 = 1405  # 0x057D
    MADC_ILOOP_RAW = 1406  # 0x057E
    MADC_DIAG_RAW = 1407  # 0x057F
    UNUSED_REG384 = 1408  # 0x0580
    UNUSED_REG385 = 1409  # 0x0581
    CALR3_DSP = 1410  # 0x0582
    PD_MADC = 1411  # 0x0583
    UNUSED_REG388 = 1412  # 0x0584
    PD_BIAS = 1413  # 0x0585
    PD_DC_ADC = 1414  # 0x0586
    PD_DC_DAC = 1415  # 0x0587
    PD_DC_SNS = 1416  # 0x0588
    PD_DC_COARSE_SNS = 1417  # 0x0589
    PD_VBAT_SNS = 1418  # 0x058A
    PD_DC_BUF = 1419  # 0x058B
    PD_AC_ADC = 1420  # 0x058C
    PD_AC_DAC = 1421  # 0x058D
    PD_AC_SNS = 1422  # 0x058E
    PD_CM_SNS = 1423  # 0x058F
    PD_CM = 1424  # 0x0590
    UNUSED_REG401 = 1425  # 0x0591
    UNUSED_REG402 = 1426  # 0x0592
    PD_SUM = 1427  # 0x0593
    PD_LKGDAC = 1428  # 0x0594
    UNUSED_REG405 = 1429  # 0x0595
    PD_HVIC = 1430  # 0x0596
    UNUSED_REG407 = 1431  # 0x0597
    CMDAC_CHEN_B = 1432  # 0x0598
    SUM_CHEN_B = 1433  # 0x0599
    TRNRD_CHEN_B = 1434  # 0x059A
    UNUSED_REG411 = 1435  # 0x059B
    DC_BUF_CHEN_B = 1436  # 0x059C
    AC_SNS_CHEN_B = 1437  # 0x059D
    DC_SNS_CHEN_B = 1438  # 0x059E
    LB_MUX_CHEN_B = 1439  # 0x059F
    UNUSED_REG416 = 1440  # 0x05A0
    CMDAC_EN_B = 1441  # 0x05A1
    RA_EN_B = 1442  # 0x05A2
    RD_EN_B = 1443  # 0x05A3
    VCTL = 1444  # 0x05A4
    UNUSED_REG421 = 1445  # 0x05A5
    UNUSED_REG422 = 1446  # 0x05A6
    HVIC_STATE = 1447  # 0x05A7
    HVIC_STATE_OBSERVE = 1448  # 0x05A8
    HVIC_STATE_MAN = 1449  # 0x05A9
    HVIC_STATE_READ = 1450  # 0x05AA
    UNUSED_REG427 = 1451  # 0x05AB
    VCMDAC_SCALE_MAN = 1452  # 0x05AC
    CAL_ACADC_CNTL = 1453  # 0x05AD
    CAL_ACDAC_CNTL = 1454  # 0x05AE
    UNUSED_REG431 = 1455  # 0x05AF
    CAL_DCDAC_CNTL = 1456  # 0x05B0
    CAL_TRNRD_CNTL = 1457  # 0x05B1
    CAL_TRNRD_DACT = 1458  # 0x05B2
    CAL_TRNRD_DACR = 1459  # 0x05B3
    LKG_UPT_ACTIVE = 1460  # 0x05B4
    LKG_UPR_ACTIVE = 1461  # 0x05B5
    LKG_DNT_ACTIVE = 1462  # 0x05B6
    LKG_DNR_ACTIVE = 1463  # 0x05B7
    LKG_UPT_OHT = 1464  # 0x05B8
    LKG_UPR_OHT = 1465  # 0x05B9
    LKG_DNT_OHT = 1466  # 0x05BA
    LKG_DNR_OHT = 1467  # 0x05BB
    CAL_LKG_EN_CNTL = 1468  # 0x05BC
    CAL_PUPD_CNTL = 1469  # 0x05BD
    UNUSED_REG446 = 1470  # 0x05BE
    CAL_AC_RCAL = 1471  # 0x05BF
    CAL_DC_RCAL = 1472  # 0x05C0
    KAC_MOD = 1473  # 0x05C1
    KAC_SEL = 1474  # 0x05C2
    SEL_RING = 1475  # 0x05C3
    CMDAC_FWD = 1476  # 0x05C4
    CMDAC_RVS = 1477  # 0x05C5
    CAL_INC_STATE = 1478  # 0x05C6
    CAL_DCDAC_COMP = 1479  # 0x05C7
    BAT_SWITCH = 1480  # 0x05C8
    CH_IRQ = 1481  # 0x05C9
    ILOOP_CROSSING = 1482  # 0x05CA
    VOC_FAILSAFE = 1483  # 0x05CB
    UNUSED_REG460 = 1484  # 0x05CC
    UNUSED_REG461 = 1485  # 0x05CD
    GENERIC_0 = 1486  # 0x05CE
    GENERIC_1 = 1487  # 0x05CF
    GENERIC_2 = 1488  # 0x05D0
    GENERIC_3 = 1489  # 0x05D1
    GENERIC_4 = 1490  # 0x05D2
    GENERIC_5 = 1491  # 0x05D3
    GENERIC_6 = 1492  # 0x05D4
    GENERIC_7 = 1493  # 0x05D5
    UNUSED_REG470 = 1494  # 0x05D6
    UNUSED_REG471 = 1495  # 0x05D7
    QHI_SET = 1496  # 0x05D8
    QHI_CLR = 1497  # 0x05D9
    UNUSED_REG474 = 1498  # 0x05DA
    RDC_SUM = 1499  # 0x05DB
    UNUSED_REG476 = 1500  # 0x05DC
    UNUSED_REG477 = 1501  # 0x05DD
    UNUSED_REG478 = 1502  # 0x05DE
    UNUSED_REG479 = 1503  # 0x05DF
    UNUSED_REG480 = 1504  # 0x05E0
    UNUSED_REG481 = 1505  # 0x05E1
    FLUSH_AUDIO_MAN = 1506  # 0x05E2
    FLUSH_DC_MAN = 1507  # 0x05E3
    TIP_RING_CNTL = 1508  # 0x05E4
    SQUELCH_SET = 1509  # 0x05E5
    SQUELCH_CLR = 1510  # 0x05E6
    CAL_STATE_MAN = 1511  # 0x05E7
    UNUSED_REG488 = 1512  # 0x05E8
    UNUSED_REG489 = 1513  # 0x05E9
    RINGING_BW = 1514  # 0x05EA
    AUDIO_MAN = 1515  # 0x05EB
    HVIC_STATE_SPARE = 1516  # 0x05EC
    RINGING_FAST_MAN = 1517  # 0x05ED
    VCM_DAC_MAN = 1518  # 0x05EE
    UNUSED_REG495 = 1519  # 0x05EF
    UNUSED_REG496 = 1520  # 0x05F0
    UNUSED_REG497 = 1521  # 0x05F1
    GENERIC_8 = 1522  # 0x05F2
    GENERIC_9 = 1523  # 0x05F3
    GENERIC_10 = 1524  # 0x05F4
    GENERIC_11 = 1525  # 0x05F5
    UNUSED_REG502 = 1526  # 0x05F6
    GENERIC_12 = 1527  # 0x05F7
    GENERIC_13 = 1528  # 0x05F8
    UNUSED_REG505 = 1529  # 0x05F9
    DC_HOLD_DAC = 1530  # 0x05FA
    OFFHOOK_CMP = 1531  # 0x05FB
    PWRSAVE_SET = 1532  # 0x05FC
    PWRSAVE_CLR = 1533  # 0x05FD
    PD_WKUP = 1534  # 0x05FE
    SPEEDUP_MASK_SET = 1535  # 0x05FF
    SPEEDUP_MASK_CLR = 1536  # 0x0600
    UNUSED_REG513 = 1537  # 0x0601
    PD_DCDC = 1538  # 0x0602
    UNUSED_REG515 = 1539  # 0x0603
    PD_UVLO = 1540  # 0x0604
    PD_OVLO = 1541  # 0x0605
    PD_OCLO = 1542  # 0x0606
    PD_SWDRV = 1543  # 0x0607
    UNUSED_REG520 = 1544  # 0x0608
    DCDC_UVHYST = 1545  # 0x0609
    DCDC_UVTHRESH = 1546  # 0x060A
    DCDC_OVTHRESH = 1547  # 0x060B
    DCDC_OITHRESH = 1548  # 0x060C
    UNUSED_REG525 = 1549  # 0x060D
    UNUSED_REG526 = 1550  # 0x060E
    DCDC_STATUS = 1551  # 0x060F
    UNUSED_REG528 = 1552  # 0x0610
    DCDC_SWDRV_POL = 1553  # 0x0611
    DCDC_UVPOL = 1554  # 0x0612
    DCDC_CPUMP = 1555  # 0x0613
    UNUSED_REG532 = 1556  # 0x0614
    DCDC_VREF_MAN = 1557  # 0x0615
    DCDC_VREF_CTRL = 1558  # 0x0616
    UNUSED_REG535 = 1559  # 0x0617
    DCDC_RNGTYPE = 1560  # 0x0618
    DCDC_DIN_FILT = 1561  # 0x0619
    UNUSED_REG538 = 1562  # 0x061A
    DCDC_DOUT = 1563  # 0x061B
    UNUSED_REG540 = 1564  # 0x061C
    DCDC_OIMASK = 1565  # 0x061D
    UNUSED_REG542 = 1566  # 0x061E
    UNUSED_REG543 = 1567  # 0x061F
    DCDC_SC_SET = 1568  # 0x0620
    WAKE_HOLD = 1569  # 0x0621
    PD_AC_SQUELCH = 1570  # 0x0622
    PD_REF_OSC = 1571  # 0x0623
    UNUSED_REG548 = 1572  # 0x0624
    PWRSAVE_MAN = 1573  # 0x0625
    PWRSAVE_SEL = 1574  # 0x0626
    PWRSAVE_CTRL_LO = 1575  # 0x0627
    PWRSAVE_CTRL_HI = 1576  # 0x0628
    PWRSAVE_HVIC_LO = 1577  # 0x0629
    PWRSAVE_HVIC_HI = 1578  # 0x062A
    DSP_PROM_MISR = 1579  # 0x062B
    DSP_CROM_MISR = 1580  # 0x062C
    DAA_PROM_MISR = 1581  # 0x062D
    DAA_CROM_MISR = 1582  # 0x062E
    RAMBIST_ERROR = 1583  # 0x062F
    DCDC_ANA_VREF = 1584  # 0x0630
    DCDC_ANA_GAIN = 1585  # 0x0631
    DCDC_ANA_TOFF = 1586  # 0x0632
    DCDC_ANA_TONMIN = 1587  # 0x0633
    DCDC_ANA_TONMAX = 1588  # 0x0634
    DCDC_ANA_DSHIFT = 1589  # 0x0635
    DCDC_ANA_LPOLY = 1590  # 0x0636
    DCDC_ANA_PSKIP = 1591  # 0x0637
    PD_DCDC_ANA = 1592  # 0x0638
    UNUSED_REG569 = 1593  # 0x0639
    UNUSED_REG570 = 1594  # 0x063A
    PWRPEND_SET = 1595  # 0x063B
    PD_CM_BUF = 1596  # 0x063C
    JMP8 = 1597  # 0x063D
    JMP9 = 1598  # 0x063E
    JMP10 = 1599  # 0x063F
    JMP11 = 1600  # 0x0640
    JMP12 = 1601  # 0x0641
    JMP13 = 1602  # 0x0642
    JMP14 = 1603  # 0x0643
    JMP15 = 1604  # 0x0644
    METER_TRIG = 1605  # 0x0645
    PM_ACTIVE = 1606  # 0x0646
    PM_INACTIVE = 1607  # 0x0647
    HVIC_VERSION = 1608  # 0x0648
    THERM_OFF = 1609  # 0x0649
    THERM_HI = 1610  # 0x064A
    TEST_LOAD = 1611  # 0x064B
    DC_HOLD_MAN = 1612  # 0x064C
    DC_HOLD_DAC_MAN = 1613  # 0x064D
    UNUSED_REG590 = 1614  # 0x064E
    DCDC_CPUMP_LP = 1615  # 0x064F
    DCDC_CPUMP_LP_MASK = 1616  # 0x0650
    DCDC_CPUMP_PULLDOWN = 1617  # 0x0651
    BOND_STATUS = 1618  # 0x0652
    BOND_MAN = 1619  # 0x0653
    BOND_VAL = 1620  # 0x0654
    REF_DEBOUNCE_PCLK = 1633  # 0x0661
    REF_DEBOUNCE_FSYNC = 1634  # 0x0662
    DCDC_LIFT_EN = 1635  # 0x0663
    DCDC_CPUMP_PGOOD = 1636  # 0x0664
    DCDC_CPUMP_PGOOD_WKEN = 1637  # 0x0665
    DCDC_CPUMP_PGOOD_FRC = 1638  # 0x0666
    DCDC_CPUMP_LP_MASK_SH = 1639  # 0x0667
    DCDC_UV_MAN = 1640  # 0x0668
    DCDC_UV_DEBOUNCE = 1641  # 0x0669
    DCDC_OV_MAN = 1642  # 0x066A
    DCDC_OV_DEBOUNCE = 1643  # 0x066B
    ANALOG3_TEST_MUX = 1644  # 0x066C
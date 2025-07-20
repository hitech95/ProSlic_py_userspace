import time
import spidev


class SPIDevice(object):
    def __init__(self, spiBus, spiDevice, spiMode, spiSpeed=100000):
        print("SPIDevice.__init__")
        super().__init__()

        self._busN = spiBus
        self._deviceN = spiDevice
        self._mode = spiMode
        self._speed = spiSpeed

    def _open(self):
        self.device = spidev.SpiDev()
        try:
            # Open SPI device
            self.device.open(self._busN, self._deviceN)

            # Set SPI mode and speed
            self.device.mode = self._mode
            self.device.max_speed_hz = self._speed
            return 0
        except Exception as e:
            print(f"Error initializing SPI device: {e}")
            return -1

    def _close(self):
        # Accessible only by child classes
        self.device.close()

    def read(self, length):
        try:
            received_data = self.device.readbytes(length)
            # print(f"Read bytes: {hex_array(received_data)}")
            return received_data
        except Exception as e:
            print(f"Error reading bytes: {e}")
            return None

    def write(self, data):
        try:
            self.device.xfer2(data)
        except Exception as e:
            print(f"Error writing bytes: {e}")

    # this is defined here as a shared common function
    def delay(self, milliseconds):
        seconds = milliseconds / 1000.0
        time.sleep(seconds)

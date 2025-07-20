from time import sleep
from sivoice.codecs.dummy import SiDummy
from sivoice.patches.patch_si32282 import Si32282Blob
from utils.spi_device import SPIDevice
# asd
print("hello!")

# print("testing SPIDevice class...")
# busDevice = SPIDevice(1, 0, 3)
# busDevice._open()
# busDevice.write([0x60, 0x00])
# readed = busDevice.read(2)
# print(readed)
# print(f"we have readed: {hex(readed[0])}")

# GPIO 25 (reset)
# BUS 1, Device 0, SPI MODE 3
print("starting SiDummy!")
dummyDevice = SiDummy(25, 1, 0, 3)
if dummyDevice.setup() < 0:
    print("Error occourred!")
    exit()

count = dummyDevice.getChannelCount()
print(f"Found {count} channels")

print("Waiting for Tests... testing chan 0")
sleep(2)
if dummyDevice.testSPI(0):
    print("Test SPI: OK")
else:
    print("Test SPI: ERR")
sleep(1)
if dummyDevice.testRAM(0):
    print("Test RAM: OK")
else:
    print("Test RAM: ERR")

blob = Si32282Blob()
dummyDevice.loadBlob(blob)

dummyDevice.close()

print("done!")

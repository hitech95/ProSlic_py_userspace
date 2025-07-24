
from enum import Enum

CHANNEL_COUNT = 2
PROSLIC_RETRIES = 10

# Known Registers that *should* be shared between devices
class ProSLIC_CommonREGs(Enum):
    ID = 0
    MSTRSTAT = 0x3
    RAM_STAT = 0x4
    RAM_ADDR_HI = 0x5
    RAM_D0 = 0x6
    RAM_D1 = 0x7
    RAM_D2 = 0x8
    RAM_D3 = 0x9
    RAM_ADDR_LO = 0xA
    PCMMODE = 0x0B
    PCMTXLO = 0x0C
    PCMTXHI = 0x0D
    PCMRXLO = 0x0E
    PCMRXHI = 0x0F
    # ...
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
    CALR0 = 0x1A
    CALR1 = 0x1B
    CALR2 = 0x1C
    CALR3 = 0x1D
    LINEFEED = 0x1E
    # ...
    LCRRTP = 0x22
    LOOPBACK = 0x2B
    ENHANCE = 0x2F
    # ...
    AUTO = 0x50
    JMPEN = 0x51
    JMP0LO = 0x52
    JMP0HI = 0x53
    JMP1LO = 0x54
    JMP1HI = 0x55
    JMP2LO = 0x56
    JMP2HI = 0x57
    JMP3LO = 0x58
    JMP3HI = 0x59
    JMP4LO = 0x5A
    JMP4HI = 0x5B
    # ...
    PDN = 0x62
    # ...
    USERMODE = 0x7E

# Known RAM Addrs that *should* be shared between devices
class ProSLIC_CommonRamAddrs(Enum):
    BLOB_ID = 0x1C0
    TEST_IO = 0x1C1
    BLOB_DATA_ADDR = 1358
    BLOB_DATA_DATA = 1359
    BLOB_JMP_TABLE2 = 0x63D
    # ...

class ProSLIC_IRQ1(Enum):
    IRQ_OSC1_T1 = 1 << 0
    IRQ_OSC1_T2 = 1 << 1
    IRQ_OSC2_T1 = 1 << 2
    IRQ_OSC2_T2 = 1 << 3
    IRQ_RING_T1 = 1 << 4
    IRQ_RING_T2 = 1 << 5
    IRQ_FSKBUF_AVAIL = 1 << 6
    IRQ_VBAT = 1 << 7

class ProSLIC_IRQ2(Enum):
    IRQ_RING_TRIP = 1 << 0
    IRQ_LOOP_STATUS = 1 << 1
    IRQ_LONG_STAT = 1 << 2
    IRQ_VOC_TRACK = 1 << 3
    IRQ_DTMF = 1 << 4
    IRQ_INDIRECT = 1 << 5
    IRQ_RXMDM = 1 << 6
    IRQ_TXMDM = 1 << 7

class ProSLIC_IRQ3(Enum):
    IRQ_P_HVIC = 1 << 0
    IRQ_P_THERM = 1 << 1
    IRQ_PQ3 = 1 << 2
    IRQ_PQ4 = 1 << 3
    IRQ_PQ5 = 1 << 4
    IRQ_PQ6 = 1 << 5
    IRQ_DSP = 1 << 6
    IRQ_MADC_FS = 1 << 7

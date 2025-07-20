
from enum import Enum

# Byte positions in the protocol.
PROSLIC_PROTO_OP_BYTE = 0
PROSLIC_PROTO_REG_BYTE = 1

# How many times we have to retry an operation?
PROSLIC_RETRIES = 10

# IDs encoded in the OPcode to configure a specific channel.
CHANNEL_IDs = [
    0x00,
    0x10,
]

# Known OP codes
class ProSLIC_OpCodes(Enum):
    CHANNEL_RD = 0x60
    CHANNEL_WR = 0x20
    BCAST      = 0x80

# Known Registers that *should* be shared between devices
class ProSLIC_CommonREGs(Enum):
    ID       = 0
    MSTRSTAT = 0x3
    RAM_STAT = 0x4
    RAM_HI   = 0x5
    RAM_D0   = 0x6
    RAM_D1   = 0x7
    RAM_D2   = 0x8
    RAM_D3   = 0x9
    RAM_LO   = 0xA
    JMPEN    = 0x51
    JMP0LO   = 0x52
    JMP0HI   = 0x53

# Known RAM Addrs that *should* be shared between devices
class ProSLIC_CommonRamAddrs(Enum):
    BLOB_ID = 0x1C0
    TEST_IO = 0x1C1
    BLOB_DATA_ADDR  = 1358
    BLOB_DATA_DATA  = 1359
    BLOB_JMP_TABLE2 = 0x63D

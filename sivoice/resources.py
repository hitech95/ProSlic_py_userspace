
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
    BCAST = 0x80


class ProSLIC_CommonREGs(Enum):
    ID = 0
    MSTRSTAT = 3
    RAM_STAT = 4
    RAM_HI = 5
    RAM_D0 = 6
    RAM_D1 = 7
    RAM_D2 = 8
    RAM_D3 = 9
    RAM_LO = 10
    JMPEN = 0x51

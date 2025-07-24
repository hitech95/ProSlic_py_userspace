
from enum import Enum

class Linefeed(Enum):
    NOP = 0
    IDLE = 1
    # This state is used between ring pulses when the phone should still be ringing.
    RING_IDLE = 2
    RINGING  =  4

class HookStatus(Enum):
    UNHOOKED = 0
    HOOKED = 1

class InterrupFlags(Enum):
    LOOP = 1 << 0

class AudioPCMFormat(Enum):
    FMT_UNKOWN_A = 0
    FMT_UNKNOWN_B = 1
    FMT_PCM = 3

class LoopbackMode(Enum):
    NONE        = 0
    LOOPBACK_A  = 1
    LOOPBACK_B  = 2

class LineTermination(Enum):
    FCC     = 0 # NA
    TBR21   = 1 # Europe
    BT3     = 2 # New Zeland
    TN12    = 3 # Australia / South Africa

class CallProgressTones(Enum):
    BUSY        = 0
    DIAL        = 1
    RINGING     = 2
    CONGESTION  = 3
    ZIP         = 4


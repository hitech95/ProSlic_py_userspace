class Registers:
    ID = 0
    RESET = 1
    MSTREN = 2
    MSTRSTAT = 3
    RAMSTAT = 4
    RAM_ADDR_HI = 5
    RAM_DATA_B0 = 6
    RAM_DATA_B1 = 7
    RAM_DATA_B2 = 8
    RAM_DATA_B3 = 9
    RAM_ADDR_LO = 10
    PCMMODE = 11
    PCMTXLO = 12
    PCMTXHI = 13
    PCMRXLO = 14
    PCMRXHI = 15
    IRQ = 16
    IRQ0 = 17
    IRQ1 = 18
    IRQ2 = 19
    IRQ3 = 20
    IRQ4 = 21
    IRQEN1 = 22
    IRQEN2 = 23
    IRQEN3 = 24
    IRQEN4 = 25
    CALR0 = 26
    CALR1 = 27
    CALR2 = 28
    CALR3 = 29
    LINEFEED = 30
    POLREV = 31
    SPEEDUP_DIS = 32
    SPEEDUP = 33
    LCRRTP = 34
    OFFLOAD = 35
    BATSELMAP = 36
    BATSEL = 37
    RINGCON = 38
    RINGTALO = 39
    RINGTAHI = 40
    RINGTILO = 41
    RINGTIHI = 42
    LOOPBACK = 43
    DIGCON = 44
    RA = 45
    ZCAL_EN = 46
    ENHANCE = 47
    OMODE = 48
    OCON = 49
    O1TALO = 50
    O1TAHI = 51
    O1TILO = 52
    O1TIHI = 53
    O2TALO = 54
    O2TAHI = 55
    O2TILO = 56
    O2TIHI = 57
    FSKDAT = 58
    FSKDEPTH = 59
    TONDTMF = 60
    TONDET = 61
    TONEN = 62
    GCI_CI = 63
    GLOBSTAT1 = 64
    GLOBSTAT2 = 65
    USERSTAT = 66
    DIAG1 = 71
    DIAG2 = 72
    CM_CLAMP = 73
    REG74 = 74
    REG75 = 75
    REG76 = 76
    REG77 = 77
    REG78 = 78
    REG79 = 79
    AUTO = 80
    JMPEN = 81
    JMP0LO = 82
    JMP0HI = 83
    JMP1LO = 84
    JMP1HI = 85
    JMP2LO = 86
    JMP2HI = 87
    JMP3LO = 88
    JMP3HI = 89
    JMP4LO = 90
    JMP4HI = 91
    JMP5LO = 92
    JMP5HI = 93
    JMP6LO = 94
    JMP6HI = 95
    JMP7LO = 96
    JMP7HI = 97
    PDN = 98
    PDN_STAT = 99

# Create a sparse lookup dictionary
register_lookup = {
    Registers.ID: "ID(g)",
    Registers.RESET: "RESET(g)",
    Registers.MSTREN: "MSTREN(g)",
    Registers.MSTRSTAT: "MSTRSTAT(g)",
    Registers.RAMSTAT: "RAMSTAT",
    Registers.RAM_ADDR_HI: "RAM_ADDR_HI",
    Registers.RAM_DATA_B0: "RAM_DATA_B0",
    Registers.RAM_DATA_B1: "RAM_DATA_B1",
    Registers.RAM_DATA_B2: "RAM_DATA_B2",
    Registers.RAM_DATA_B3: "RAM_DATA_B3",
    Registers.RAM_ADDR_LO: "RAM_ADDR_LO",
    Registers.PCMMODE: "PCMMODE",
    Registers.PCMTXLO: "PCMTXLO",
    Registers.PCMTXHI: "PCMTXHI",
    Registers.PCMRXLO: "PCMRXLO",
    Registers.PCMRXHI: "PCMRXHI",
    Registers.IRQ: "IRQ(g)",
    Registers.IRQ0: "IRQ0",
    Registers.IRQ1: "IRQ1",
    Registers.IRQ2: "IRQ2",
    Registers.IRQ3: "IRQ3",
    Registers.IRQ4: "IRQ4",
    Registers.IRQEN1: "IRQEN1",
    Registers.IRQEN2: "IRQEN2",
    Registers.IRQEN3: "IRQEN3",
    Registers.IRQEN4: "IRQEN4",
    Registers.CALR0: "CALR0",
    Registers.CALR1: "CALR1",
    Registers.CALR2: "CALR2",
    Registers.CALR3: "CALR3",
    Registers.LINEFEED: "LINEFEED",
    Registers.POLREV: "POLREV",
    Registers.SPEEDUP_DIS: "SPEEDUP_DIS",
    Registers.SPEEDUP: "SPEEDUP",
    Registers.LCRRTP: "LCRRTP",
    Registers.OFFLOAD: "OFFLOAD",
    Registers.BATSELMAP: "BATSELMAP",
    Registers.BATSEL: "BATSEL",
    Registers.RINGCON: "RINGCON",
    Registers.RINGTALO: "RINGTALO",
    Registers.RINGTAHI: "RINGTAHI",
    Registers.RINGTILO: "RINGTILO",
    Registers.RINGTIHI: "RINGTIHI",
    Registers.LOOPBACK: "LOOPBACK",
    Registers.DIGCON: "DIGCON",
    Registers.RA: "RA",
    Registers.ZCAL_EN: "ZCAL_EN",
    Registers.ENHANCE: "ENHANCE",
    Registers.OMODE: "OMODE",
    Registers.OCON: "OCON",
    Registers.O1TALO: "O1TALO",
    Registers.O1TAHI: "O1TAHI",
    Registers.O1TILO: "O1TILO",
    Registers.O1TIHI: "O1TIHI",
    Registers.O2TALO: "O2TALO",
    Registers.O2TAHI: "O2TAHI",
    Registers.O2TILO: "O2TILO",
    Registers.O2TIHI: "O2TIHI",
    Registers.FSKDAT: "FSKDAT",
    Registers.FSKDEPTH: "FSKDEPTH",
    Registers.TONDTMF: "TONDTMF",
    Registers.TONDET: "TONDET",
    Registers.TONEN: "TONEN",
    Registers.GCI_CI: "GCI_CI",
    Registers.GLOBSTAT1: "GLOBSTAT1(g)",
    Registers.GLOBSTAT2: "GLOBSTAT2(g)",
    Registers.USERSTAT: "USERSTAT",
    Registers.DIAG1: "DIAG1",
    Registers.DIAG2: "DIAG2",
    Registers.CM_CLAMP: "CM_CLAMP",
    Registers.REG74: "REG74",
    Registers.REG75: "REG75",
    Registers.REG76: "REG76",
    Registers.REG77: "REG77",
    Registers.REG78: "REG78",
    Registers.REG79: "REG79",
    Registers.AUTO: "AUTO(g)",
    Registers.JMPEN: "JMPEN",
    Registers.JMP0LO: "JMP0LO",
    Registers.JMP0HI: "JMP0HI",
    Registers.JMP1LO: "JMP1LO",
    Registers.JMP1HI: "JMP1HI",
    Registers.JMP2LO: "JMP2LO",
    Registers.JMP2HI: "JMP2HI",
    Registers.JMP3LO: "JMP3LO",
    Registers.JMP3HI: "JMP3HI",
    Registers.JMP4LO: "JMP4LO",
    Registers.JMP4HI: "JMP4HI",
    Registers.JMP5LO: "JMP5LO",
    Registers.JMP5HI: "JMP5HI",
    Registers.JMP6LO: "JMP6LO",
    Registers.JMP6HI: "JMP6HI",
    Registers.JMP7LO: "JMP7LO",
    Registers.JMP7HI: "JMP7HI",
    Registers.PDN: "PDN",
    Registers.PDN_STAT: "PDN_STAT",
}

def get_register_name(address):
    return register_lookup.get(address, f"Unknown ({hex(address)})")
 

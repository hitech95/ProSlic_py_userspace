class Registers:
    ID = 0  # 0x0000
    RESET = 1  # 0x0001
    MSTREN = 2  # 0x0002
    MSTRSTAT = 3  # 0x0003
    RAMSTAT = 4  # 0x0004
    RAM_ADDR_HI = 5  # 0x0005
    RAM_DATA_B0 = 6  # 0x0006
    RAM_DATA_B1 = 7  # 0x0007
    RAM_DATA_B2 = 8  # 0x0008
    RAM_DATA_B3 = 9  # 0x0009
    RAM_ADDR_LO = 10  # 0x000A
    PCMMODE = 11  # 0x000B
    PCMTXLO = 12  # 0x000C
    PCMTXHI = 13  # 0x000D
    PCMRXLO = 14  # 0x000E
    PCMRXHI = 15  # 0x000F
    IRQ = 16  # 0x0010
    IRQ0 = 17  # 0x0011
    IRQ1 = 18  # 0x0012
    IRQ2 = 19  # 0x0013
    IRQ3 = 20  # 0x0014
    IRQ4 = 21  # 0x0015
    IRQEN1 = 22  # 0x0016
    IRQEN2 = 23  # 0x0017
    IRQEN3 = 24  # 0x0018
    IRQEN4 = 25  # 0x0019
    CALR0 = 26  # 0x001A
    CALR1 = 27  # 0x001B
    CALR2 = 28  # 0x001C
    CALR3 = 29  # 0x001D
    LINEFEED = 30  # 0x001E
    POLREV = 31  # 0x001F
    SPEEDUP_DIS = 32  # 0x0020
    SPEEDUP = 33  # 0x0021
    LCRRTP = 34  # 0x0022
    OFFLOAD = 35  # 0x0023
    BATSELMAP = 36  # 0x0024
    BATSEL = 37  # 0x0025
    RINGCON = 38  # 0x0026
    RINGTALO = 39  # 0x0027
    RINGTAHI = 40  # 0x0028
    RINGTILO = 41  # 0x0029
    RINGTIHI = 42  # 0x002A
    LOOPBACK = 43  # 0x002B
    DIGCON = 44  # 0x002C
    RA = 45  # 0x002D
    ZCAL_EN = 46  # 0x002E
    ENHANCE = 47  # 0x002F
    OMODE = 48  # 0x0030
    OCON = 49  # 0x0031
    O1TALO = 50  # 0x0032
    O1TAHI = 51  # 0x0033
    O1TILO = 52  # 0x0034
    O1TIHI = 53  # 0x0035
    O2TALO = 54  # 0x0036
    O2TAHI = 55  # 0x0037
    O2TILO = 56  # 0x0038
    O2TIHI = 57  # 0x0039
    FSKDAT = 58  # 0x003A
    FSKDEPTH = 59  # 0x003B
    TONDTMF = 60  # 0x003C
    TONDET = 61  # 0x003D
    TONEN = 62  # 0x003E
    GCI_CI = 63  # 0x003F
    GLOBSTAT1 = 64  # 0x0040
    GLOBSTAT2 = 65  # 0x0041
    USERSTAT = 66  # 0x0042
    GPIO_CFG1 = 68  # 0x0044
    DIAG1 = 71  # 0x0047
    DIAG2 = 72  # 0x0048
    CM_CLAMP = 73  # 0x0049
    DIAG3 = 74  # 0x004A
    PMCON = 75  # 0x004B
    PCLK_FAULT_CNTL = 76  # 0x004C
    AUTO = 80  # 0x0050
    JMPEN = 81  # 0x0051
    JMP0LO = 82  # 0x0052
    JMP0HI = 83  # 0x0053
    JMP1LO = 84  # 0x0054
    JMP1HI = 85  # 0x0055
    JMP2LO = 86  # 0x0056
    JMP2HI = 87  # 0x0057
    JMP3LO = 88  # 0x0058
    JMP3HI = 89  # 0x0059
    JMP4LO = 90  # 0x005A
    JMP4HI = 91  # 0x005B
    JMP5LO = 92  # 0x005C
    JMP5HI = 93  # 0x005D
    JMP6LO = 94  # 0x005E
    JMP6HI = 95  # 0x005F
    JMP7LO = 96  # 0x0060
    JMP7HI = 97  # 0x0061
    PDN = 98  # 0x0062
    PDN_STAT = 99  # 0x0063
    PDN2 = 100  # 0x0064
    PDN2_STAT = 101  # 0x0065
    M1_OSC_LO = 112  # 0x0070
    M1_OSC_HI = 113  # 0x0071
    BITCNT_LO = 114  # 0x0072
    BITCNT_HI = 115  # 0x0073
    PCLK_MULT = 116  # 0x0074
    RAM_DATA_16 = 117  # 0x0075
    BYPASS_ADDR_LO = 118  # 0x0076
    BYPASS_ADDR_HI = 119  # 0x0077
    PC_LO = 120  # 0x0078
    PC_HI = 121  # 0x0079
    PC_SHAD_LO = 122  # 0x007A
    PC_SHAD_HI = 123  # 0x007B
    PASS_LO = 124  # 0x007C
    PASS_HI = 125  # 0x007D
    TEST_CNTL = 126  # 0x007E
    TEST_MODE = 127  # 0x007F


register_lookup = {
    Registers.ID: "ID(g)",  # 0x0000
    Registers.RESET: "RESET(g)",  # 0x0001
    Registers.MSTREN: "MSTREN(g)",  # 0x0002
    Registers.MSTRSTAT: "MSTRSTAT(g)",  # 0x0003
    Registers.RAMSTAT: "RAMSTAT",  # 0x0004
    Registers.RAM_ADDR_HI: "RAM_ADDR_HI(g)",  # 0x0005
    Registers.RAM_DATA_B0: "RAM_DATA_B0(g)",  # 0x0006
    Registers.RAM_DATA_B1: "RAM_DATA_B1(g)",  # 0x0007
    Registers.RAM_DATA_B2: "RAM_DATA_B2(g)",  # 0x0008
    Registers.RAM_DATA_B3: "RAM_DATA_B3(g)",  # 0x0009
    Registers.RAM_ADDR_LO: "RAM_ADDR_LO(g)",  # 0x000A
    Registers.PCMMODE: "PCMMODE(g)",  # 0x000B
    Registers.PCMTXLO: "PCMTXLO(g)",  # 0x000C
    Registers.PCMTXHI: "PCMTXHI(g)",  # 0x000D
    Registers.PCMRXLO: "PCMRXLO(g)",  # 0x000E
    Registers.PCMRXHI: "PCMRXHI(g)",  # 0x000F
    Registers.IRQ: "IRQ(g)",  # 0x0010
    Registers.IRQ0: "IRQ0(g)",  # 0x0011
    Registers.IRQ1: "IRQ1(g)",  # 0x0012
    Registers.IRQ2: "IRQ2(g)",  # 0x0013
    Registers.IRQ3: "IRQ3(g)",  # 0x0014
    Registers.IRQ4: "IRQ4(g)",  # 0x0015
    Registers.IRQEN1: "IRQEN1(g)",  # 0x0016
    Registers.IRQEN2: "IRQEN2(g)",  # 0x0017
    Registers.IRQEN3: "IRQEN3(g)",  # 0x0018
    Registers.IRQEN4: "IRQEN4(g)",  # 0x0019
    Registers.CALR0: "CALR0(g)",  # 0x001A
    Registers.CALR1: "CALR1(g)",  # 0x001B
    Registers.CALR2: "CALR2(g)",  # 0x001C
    Registers.CALR3: "CALR3(g)",  # 0x001D
    Registers.LINEFEED: "LINEFEED(g)",  # 0x001E
    Registers.POLREV: "POLREV(g)",  # 0x001F
    Registers.SPEEDUP_DIS: "SPEEDUP_DIS(g)",  # 0x0020
    Registers.SPEEDUP: "SPEEDUP(g)",  # 0x0021
    Registers.LCRRTP: "LCRRTP(g)",  # 0x0022
    Registers.OFFLOAD: "OFFLOAD(g)",  # 0x0023
    Registers.BATSELMAP: "BATSELMAP(g)",  # 0x0024
    Registers.BATSEL: "BATSEL(g)",  # 0x0025
    Registers.RINGCON: "RINGCON(g)",  # 0x0026
    Registers.RINGTALO: "RINGTALO(g)",  # 0x0027
    Registers.RINGTAHI: "RINGTAHI(g)",  # 0x0028
    Registers.RINGTILO: "RINGTILO(g)",  # 0x0029
    Registers.RINGTIHI: "RINGTIHI(g)",  # 0x002A
    Registers.LOOPBACK: "LOOPBACK(g)",  # 0x002B
    Registers.DIGCON: "DIGCON(g)",  # 0x002C
    Registers.RA: "RA(g)",  # 0x002D
    Registers.ZCAL_EN: "ZCAL_EN(g)",  # 0x002E
    Registers.ENHANCE: "ENHANCE(g)",  # 0x002F
    Registers.OMODE: "OMODE(g)",  # 0x0030
    Registers.OCON: "OCON(g)",  # 0x0031
    Registers.O1TALO: "O1TALO(g)",  # 0x0032
    Registers.O1TAHI: "O1TAHI(g)",  # 0x0033
    Registers.O1TILO: "O1TILO(g)",  # 0x0034
    Registers.O1TIHI: "O1TIHI(g)",  # 0x0035
    Registers.O2TALO: "O2TALO(g)",  # 0x0036
    Registers.O2TAHI: "O2TAHI(g)",  # 0x0037
    Registers.O2TILO: "O2TILO(g)",  # 0x0038
    Registers.O2TIHI: "O2TIHI(g)",  # 0x0039
    Registers.FSKDAT: "FSKDAT(g)",  # 0x003A
    Registers.FSKDEPTH: "FSKDEPTH(g)",  # 0x003B
    Registers.TONDTMF: "TONDTMF(g)",  # 0x003C
    Registers.TONDET: "TONDET(g)",  # 0x003D
    Registers.TONEN: "TONEN(g)",  # 0x003E
    Registers.GCI_CI: "GCI_CI(g)",  # 0x003F
    Registers.GLOBSTAT1: "GLOBSTAT1(g)",  # 0x0040
    Registers.GLOBSTAT2: "GLOBSTAT2(g)",  # 0x0041
    Registers.USERSTAT: "USERSTAT(g)",  # 0x0042
    Registers.GPIO_CFG1: "GPIO_CFG1(g)",  # 0x0044
    Registers.DIAG1: "DIAG1(g)",  # 0x0047
    Registers.DIAG2: "DIAG2(g)",  # 0x0048
    Registers.CM_CLAMP: "CM_CLAMP(g)",  # 0x0049
    Registers.DIAG3: "DIAG3(g)",  # 0x004A
    Registers.PMCON: "PMCON(g)",  # 0x004B
    Registers.PCLK_FAULT_CNTL: "PCLK_FAULT_CNTL(g)",  # 0x004C
    Registers.AUTO: "AUTO(g)",  # 0x0050
    Registers.JMPEN: "JMPEN(g)",  # 0x0051
    Registers.JMP0LO: "JMP0LO(g)",  # 0x0052
    Registers.JMP0HI: "JMP0HI(g)",  # 0x0053
    Registers.JMP1LO: "JMP1LO(g)",  # 0x0054
    Registers.JMP1HI: "JMP1HI(g)",  # 0x0055
    Registers.JMP2LO: "JMP2LO(g)",  # 0x0056
    Registers.JMP2HI: "JMP2HI(g)",  # 0x0057
    Registers.JMP3LO: "JMP3LO(g)",  # 0x0058
    Registers.JMP3HI: "JMP3HI(g)",  # 0x0059
    Registers.JMP4LO: "JMP4LO(g)",  # 0x005A
    Registers.JMP4HI: "JMP4HI(g)",  # 0x005B
    Registers.JMP5LO: "JMP5LO(g)",  # 0x005C
    Registers.JMP5HI: "JMP5HI(g)",  # 0x005D
    Registers.JMP6LO: "JMP6LO(g)",  # 0x005E
    Registers.JMP6HI: "JMP6HI(g)",  # 0x005F
    Registers.JMP7LO: "JMP7LO(g)",  # 0x0060
    Registers.JMP7HI: "JMP7HI(g)",  # 0x0061
    Registers.PDN: "PDN(g)",  # 0x0062
    Registers.PDN_STAT: "PDN_STAT(g)",  # 0x0063
    Registers.PDN2: "PDN2(g)",  # 0x0064
    Registers.PDN2_STAT: "PDN2_STAT(g)",  # 0x0065
    Registers.M1_OSC_LO: "M1_OSC_LO(g)",  # 0x0070
    Registers.M1_OSC_HI: "M1_OSC_HI(g)",  # 0x0071
    Registers.BITCNT_LO: "BITCNT_LO(g)",  # 0x0072
    Registers.BITCNT_HI: "BITCNT_HI(g)",  # 0x0073
    Registers.PCLK_MULT: "PCLK_MULT(g)",  # 0x0074
    Registers.RAM_DATA_16: "RAM_DATA_16(g)",  # 0x0075
    Registers.BYPASS_ADDR_LO: "BYPASS_ADDR_LO(g)",  # 0x0076
    Registers.BYPASS_ADDR_HI: "BYPASS_ADDR_HI(g)",  # 0x0077
    Registers.PC_LO: "PC_LO(g)",  # 0x0078
    Registers.PC_HI: "PC_HI(g)",  # 0x0079
    Registers.PC_SHAD_LO: "PC_SHAD_LO(g)",  # 0x007A
    Registers.PC_SHAD_HI: "PC_SHAD_HI(g)",  # 0x007B
    Registers.PASS_LO: "PASS_LO(g)",  # 0x007C
    Registers.PASS_HI: "PASS_HI(g)",  # 0x007D
    Registers.TEST_CNTL: "TEST_CNTL(g)",  # 0x007E
    Registers.TEST_MODE: "TEST_MODE(g)",  # 0x007F
}
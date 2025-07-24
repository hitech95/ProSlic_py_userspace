#!/usr/bin/env python3
import csv
import time

from core.device import SiDevice

def process_csv(device: SiDevice, csv_file):
    with open(csv_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, start=1):
            op = row['OPCODE'].strip().upper()
            channel = int(row['CHANNEL'])
            reg = row['REG'].strip() if row['REG'] else ''
            ram_addr = row['RAM_ADDR'].strip() if row['RAM_ADDR'] else ''
            raw_data = int(row['RAW_DATA'], 16)

            if reg:
                addr = int(reg, 16)
            elif ram_addr:
                addr = int(ram_addr, 16)
            else:
                print(f"[{i}] ERROR: Missing REG or RAM_ADDR")
                continue

            try:
                if op == 'WRITE':
                    device.writeRegister(channel, addr, raw_data)
                    print(f"[{i}] WRITE REG  ch={channel} addr=0x{addr:X} val=0x{raw_data:X}")
                    time.sleep(0.05)
                elif op == 'READ':
                    val = device.readRegister(channel, addr)
                    print(f"[{i}] READ  REG  ch={channel} addr=0x{addr:X} => 0x{val:X}")
                    expected_val = raw_data & 0xFF  # Only compare the lower 8 bits
                    if val != expected_val:
                        print(f"[{i}]   MISMATCH: expected 0x{expected_val:X}")
                elif op == 'RAM-WRITE':
                    device.writeRam(channel, addr, raw_data)
                    print(f"[{i}] WRITE RAM ch={channel} addr=0x{addr:X} val=0x{raw_data:X}")
                elif op == 'RAM-READ':
                    val = device.readRam(channel, addr)
                    print(f"[{i}] READ  RAM ch={channel} addr=0x{addr:X} => 0x{val:X}")
                    if val != raw_data:
                        print(f"[{i}]   MISMATCH: expected 0x{raw_data:X}")
                else:
                    print(f"[{i}] ERROR: Unknown OPCODE '{op}'")
            except Exception as e:
                print(f"[{i}] ERROR during {op}: {e}")
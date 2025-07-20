import csv
import argparse
from enum import Enum
from prettytable import PrettyTable
import traceback

from . import registers

# Add more entries for other operations as needed
class OperationCodes(Enum):
    WRITE = 0x20
    READ = 0x60
    
# Operation lookup table
operation_lookup = {
    0x60: "READ",
    0x20: "WRITE",   
}
    
# Channel lookup table
channel_lookup = {
    0x00: 0, 0x10: 1,
    # Add more entries as needed
}

ramration_lookup = {
    0x60: "RAM-READ",
    0x20: "RAM-WRITE",   
}

def read_csv(file_path):
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader, None)  # Skip the header line

        for row in csv_reader:
            timestamp = float(row[0])
            mosi_data = int(row[2], 0)
            miso_data = int(row[3], 0)
            yield timestamp, mosi_data, miso_data
    
def decode_opcode(opcode):
    # Extracting operation and channel
    operation_and_channel = (opcode >> 8) & 0xFF
    operation = operation_and_channel & 0xE0 # Assuming operation is 3 bits wide
    channel = operation_and_channel & 0x1F  # Assuming channel is 5 bits wide

    # Extracting register address
    register_addr = opcode & 0xFF

    return {
        "op": operation,
        "chan": channel,
        "reg": register_addr,
    }

def getDataForOpCode(csv_generator, op_code):
    # What data has been send or received?
    data = 0x00
    # This is only known for some operations
    if op_code == OperationCodes.READ.value:
        _, __, read = next(csv_generator)
        data = read
    elif op_code == OperationCodes.WRITE.value:
        _, wrote, __ = next(csv_generator)
        data = wrote
    else:
        data = 0xFF
    
    return data

def isMemWait(csv_generator, decoded, forward = False):
    data = None

    op_code = decoded.get("op", None)
    op_reg = decoded.get("reg", None)

    if op_reg != registers.Registers.RAMSTAT:
        return False, None
    else:
        # print(f"RAM WAIT: {operation_lookup.get(op_code)}")
        if forward:
            # Extract READ for Ram-Wait Operation
            data = getDataForOpCode(csv_generator, op_code)

        return True, data

def decodeMemoryPrint(csv_generator, table, decoded, rawData, delayMs, printRaw):
    # All the fields we have to fill in the decode process
    ramAddrHI = 0xFF
    ramAddrLO = 0xFF
    ramOPCode = 0
    ramData = 0x00
    # WRITE operations send data before RAM LOW
    isRead = False

    # Get the channel we are processing the data
    op_chan = decoded.get("chan", None)

    byteCount = 0
    while True:
        try:
            # If is ram wait forward cursor to right point
            isWait, data = isMemWait(csv_generator, decoded, True)
            
            op_code = decoded.get("op", None)
            op_reg = decoded.get("reg", None)

            # print(f"mem decoded: code={operation_lookup.get(op_code)} reg={hex(op_reg)} wait={isWait}")

            if isWait:
                # If RAM operation is complete exit loop
                if ramOPCode and (data & 0x01) == 0:
                    # print("found wait, complete")               
                    break
                else:
                    # print("found wait, continue")
                    # Extract next data to be processed
                    _, mosi_data, miso_data = next(csv_generator)
                    decoded = decode_opcode(mosi_data)
                    continue                    

            # If the operation is the one of the register we might be in READ or WRITE mode
            if  op_reg in [registers.Registers.RAM_ADDR_HI, registers.Registers.RAM_ADDR_LO]:
                # print("RAM: found address sooo .... what?")

                pass
            elif op_reg in [
                registers.Registers.RAM_DATA_B0,
                registers.Registers.RAM_DATA_B1,
                registers.Registers.RAM_DATA_B2,
                registers.Registers.RAM_DATA_B3,
            ]:
                # print("RAM: found data sooo .... what?")
                
                byteCount += 1
                ramOPCode = op_code
                isRead = op_code == 0x60
            else:
                # print(f"Uhm WTF! ... {decoded}")

                continue

            # Extract the data
            data = getDataForOpCode(csv_generator, op_code) & 0xFF

            if op_reg == registers.Registers.RAM_ADDR_HI:
                ramAddrHI = data
            elif op_reg == registers.Registers.RAM_ADDR_LO:
                ramAddrLO = data
            elif op_reg == registers.Registers.RAM_DATA_B0:
                ramData = ramData | (data >> 3)            
            elif op_reg == registers.Registers.RAM_DATA_B1:
                ramData = ramData | (data << 5)
            elif op_reg == registers.Registers.RAM_DATA_B2:
                ramData = ramData | (data << 13)
            elif op_reg == registers.Registers.RAM_DATA_B3:
                ramData = ramData | (data << 21)
            else:
                print(f"Unknown register {hex(op_reg)}!?")

            # If this is a read, the second wait is alrady processed. 
            # Exit after reading last byte, MSB first
            if isRead and byteCount == 4:
                # print(f"Exit: isRead={isRead} count={byteCount}")
                break

            # Extract next data to be processed
            _, mosi_data, miso_data = next(csv_generator)
            decoded = decode_opcode(mosi_data)
            continue
        except Exception as e:
            print("exception?")
            print(str(e))
            print(type(e))
            traceback.print_exc()
            break
    
    ramAddr = (ramAddrHI << 3) | ramAddrLO

    operation_str = ramration_lookup.get(ramOPCode, f"Ukn RAM OP({hex(ramOPCode)})")
    channel_str = channel_lookup.get(op_chan, f"Unknown ({hex(op_chan)})")

    table.add_row([f"{operation_str}", f"{channel_str}", "" , f"{hex(ramAddr)}", f"{hex(ramData)}", f"{delayMs:.3f}"])

    # print("mem-done!")

def decodeRegisterPrint(csv_generator, table, decoded, rawData, delayMs, printRaw):
    op_code = decoded.get("op", None)
    op_chan = decoded.get("chan", None)
    op_reg = decoded.get("reg", None)
    
    data = getDataForOpCode(csv_generator, op_code)
    
    # Decoding channel and operation using lookup tables
    operation_str = operation_lookup.get(op_code, f"Unknown ({hex(op_code)})")
    channel_str = channel_lookup.get(op_chan, f"Unknown ({hex(op_chan)})")
    register_str = registers.get_register_name(op_reg) if not printRaw else hex(op_reg)
    
    #table.add_row([f"{hex(mosi_data)}", f"{hex(miso_data)}"])
    table.add_row([f"{operation_str}", f"{channel_str}", f"{register_str}", "" , f"{hex(data)}", f"{delayMs:.3f}"])
    #f"{hex(mosi_data)}"

def main():
    parser = argparse.ArgumentParser(description="Decode register/memory operations")
    parser.add_argument("file", help="CSV file to process")
    parser.add_argument("-c", "--csv", help="Output decoded data to a CSV file")
    parser.add_argument("-X", "--raw", action="store_true", help="Print raw register/memory addresses (hex)")
    args = parser.parse_args()
    
    # Get the file path from the command-line arguments
    file_path = args.file
    # Create a generator
    csv_generator = read_csv(file_path)
    
    # Create a PrettyTable instance
    table = PrettyTable()
    table.field_names = ["OPCODE", "CHANNEL", "REG", "RAM_ADDR", "RAW_DATA", "DELAY_MS"]

    prev_timestamp = None

    # Iterate over the generator
    # for data in csv_generator
    line = 2
    while True:
        try:
            rawData = next(csv_generator)
            timestamp, mosi_data, miso_data = rawData
            decoded = decode_opcode(mosi_data)

            delayMs = 0
            if prev_timestamp is not None:
                delayMs = (timestamp - prev_timestamp) * 1000  # seconds → ms
            prev_timestamp = timestamp

            inMemory, _ = isMemWait(csv_generator, decoded)
            if inMemory:
                decodeMemoryPrint(csv_generator, table, decoded, rawData, delayMs, args.raw)
            else:
                decodeRegisterPrint(csv_generator, table, decoded, rawData, delayMs, args.raw)
        except StopIteration:
            break
        line += 1

    if args.csv:
        with open(args.csv, 'w', newline='') as f_output:
            f_output.write(table.get_csv_string())
    else:
        # Print the table
        print(table)
        # print("done")

if __name__ == "__main__":
    main()



#!/bin/env python3

import spidev
import time
import logging
import argparse
from sys import argv

from gpio import pin_init, OutPin

#  Flasher for AVR (serial programming)    
#
#  
#  RPi header
#                      __
#              3.3  1 |..|
#   RESET <--  GP2  3 |..|
#                     |..| 6  GND
#                     |..|
#                     |..|
#                     |..|
#                     |..|
#                     |..|
#                     |..|
#   <-- SPI0_MOSI  19 |..|
#   --> SPI0_MISO  21 |..|
#   --> SPI0_SCLK  23 |..|
#                     |..|
#

GPIO_RESET = 2
SPI_DEVICE = 0
HI_SPEED_LIMIT_HZ = 100000
LO_SPEED_LIMIT_HZ = 10000
TIMEOUT = 1.0

# Microcontroller support
MCUS = {
    "attiny13" : {
        "program_memory_size" : 1024,
        "page_size" : 32
    },
}

class MCU:
    def __init__(self, name, properties):
        self.name = name
        self.program_capacity_b = properties["program_memory_size"]
        self.program_capacity_words = properties["program_memory_size"] / 2
        self.page_size = properties["page_size"]

class Klucha:
    def __init__(self, mcu, low_speed = False):
        pin_init()
        self._mcu = mcu
        self._reset = OutPin(GPIO_RESET)
        self._spi = spidev.SpiDev()
        self._spi.open(SPI_DEVICE, 0)
        if low_speed:
            self._spi.max_speed_hz = LO_SPEED_LIMIT_HZ
        else:
            self._spi.max_speed_hz = HI_SPEED_LIMIT_HZ
        self._spi.mode = 0
        self._spi.no_cs = True
        self._spi.lsbfirst = False
        self._spi.bits_per_word = 8
        
    def enableProgramming(self):
        """
        Enable programming.
        Performs all steps to prepare for programming, including reset, reset-delay,
        sending enable-programming command and checking if command was copied back.
        It can be run alone, to check if programming interface is connected correctly.
        """
        self._reset.low()
        time.sleep(0.03)
        self._txrx([0xAC, 0x53, 0x69, 0x69])
    
    def disableProgramming(self):
        """
        Disables programming by deasserting reset.
        Useful to cancel enable-programming, or for
        resetting and trying again.
        """
        self._reset.high()
        time.sleep(0.05)    
        
    def chipErase(self):
        """
        Perform full chip erase.
        Erases chip and waits for it to finish.
        Mandatory, before re-programming chip.
        """
        self._txrx([0xAC, 0x80, 0x42, 0x42])
        self._waitUntilDone()
        
    def readProgramMemory(self, address):
        """
        Read program memory.
        Reads single byte from program memory and returns it.
        For convenience address is a byte address (function calculates
        word address itself)!
        """
        wordAddress = address >> 1
        assert wordAddress < self._mcu.program_capacity_words, "Address out of range for " + self._mcu.name
        if address & 0x1:
            return self._txrx([0x28, wordAddress >> 8, wordAddress & 0xFF, 0x00], "...o")[0]
        else:
            return self._txrx([0x20, wordAddress >> 8, wordAddress & 0xFF, 0x00], "...o")[0]
            
    def loadProgramMemoryPage(self, address, dataByte):
        """
        Load program memory page.
        Uses program memory page command. Part of programming
        (page buffer must be loaded first, then entire page can be written).
        For correct programming, load and write page commands must be done in
        correct order! It is better to use Kluchomat.program function which 
        does it all automatically.
        For convenience address is a byte address (function calculates
        word address itself)!
        """
        wordAddress = address >> 1
        assert wordAddress < self._mcu.program_capacity_words, "Address out of range for " + self._mcu.name
        if address & 0x1:
            self._txrx([0x48, 0x00, wordAddress & 0xFF, dataByte])
        else:
            self._txrx([0x40, 0x00, wordAddress & 0xFF, dataByte])
            
    def writeProgramMemoryPage(self, address):
        """
        Write program memory page.
        Uses program memory page command. Part of programming
        (page buffer must be loaded first, then entire page can be written).
        For correct programming, load and write page commands must be done in
        correct order! It is better to use Kluchomat.program function which 
        does it all automatically.
        For convenience address is a byte address (function calculates
        word address itself)!
        """
        wordAddress = address >> 1
        assert wordAddress < self._mcu.program_capacity_words, "Address out of range for " + self._mcu.name
        self._txrx([0x4C, wordAddress >> 8, wordAddress & 0xFF, 0x00])
        self._waitUntilDone()
        
    def readFuseByte(self, byteNo):
        """
        Read fuse byte.
        """
        byte_sel = (byteNo & 1) << 3
        return self._txrx([0x50 | byte_sel, byte_sel, 0x21, 0x37], "...o")[0]
        
    def writeFuseByte(self, byteNo, value):
        """
        Write fuse byte.
        """
        byte_sel = (byteNo & 1) << 3
        self._txrx([0xAC, 0xA0 | byte_sel, 0x00, value])
        self._waitUntilDone()
        
    def readLockBits(self):
        """
        Read lock bits.
        """
        return self._txrx([0x58, 0x00, 0x00, 0x00], "...o")[0] & 0x3F
        
    def readSignatureByte(self, address):
        """
        Read signature byte.
        """
        return self._txrx([0x30, 0x12, address, 0x00], "...o")[0]
        
    def readCalibrationByte(self, byteNo):
        """
        Read calibration byte.
        """
        return self._txrx([0x38, 0x12, byteNo & 1, 0x00], "...o")[0]
        
    def program(self, data):
        """
        Flash program memory.
        Copies data to program memory at offset 0.
        """
        assert len(data) <= self._mcu.program_capacity_b, "Data too long for " + self._mcu.name
        page_size = self._mcu.page_size
        pagePad = page_size - (len(data) % page_size)
        data += b"\xFF" * pagePad
        
        for i in range(0, len(data), page_size):
            logging.info("Programming page %d..." % i)
            for j in range(page_size):
                self.loadProgramMemoryPage(i+j, data[i+j])
            self.writeProgramMemoryPage(i)

    def verify(self, data):
        """
        Verify program memory contents, by reading it and
        comparing to given data. Reading starts at offset 0.
        """
        assert len(data) <= self._mcu.program_capacity_b, "Data too long for " + self._mcu.name
        for i, b in enumerate(data):
            read = self.readProgramMemory(i)
            if b != read:
                logging.error("Program verify failed @x03X %02X != %02X",
                        i, b, read)
                return False
        return True
        
    def pollReady(self):
        """
        Use pollRDY/!BSY command to check if flasher is busy.
        Returs 1 if busy, 0 if idle.
        """
        return self._txrx([0xF0, 0x00, 0x12, 0x34], "...o")[0] & 0x01
    
    def close(self):
        """
        Deinit flasher, also dessert RESET.
        """
        self._spi.close()
        self._reset.high()
        
    def getMcu(self):
        return self._mcu
        
    def _txrx(self, data, mask = None):
        if mask is None:
            mask = data
        assert len(mask) == len(data), "Wrong mask"
        resp = self._spi.xfer(data)
        assert len(resp) == len(mask), "Invalid reponse length"
        out = []
        for i, b in enumerate(resp):
            if mask[i] == 'o':
                out.append(b)
            elif mask[i] in ('x', 'i'):
                pass
            elif data[i] != b:
                logging.error("Out of sync TX:%s RX:%s", data, resp)
                raise AssertionError("Out of sync")
        return out

    def _waitUntilDone(self):
        tstart = time.time()
        while 0 != self.pollReady():
            if time.time() - tstart > TIMEOUT:
                logging.error("Timeout")
                raise Exception("Timeout")
        
def get_mcu(args):
    name = args.mcu
    props = MCUS[name]
    return MCU(name, props)
    
def list_mcus():
    for name in MCUS:
        print(name)
        
def write_file(flasher, fname, length):
    with open(fname, "rb") as fp:
        if length is None:
            data = fp.read()
        else:
            data = fp.read(length)
            
        logging.info("Loaded %d bytes from \"%s\"", len(data), fname)
        
        assert len(data) > 0, "Empty data"
        assert len(data) <= flasher.getMcu().program_capacity_b, "Data too long"
        
        logging.info("Erasing...")
        flasher.chipErase()
        logging.info("Programming...")
        flasher.program(data)
        logging.info("Verifying...")
        flasher.verify(data)
        
def dump_flash(flasher, fname, length, quiet):
    mcu = flasher.getMcu()
    
    if length is None:
        length = mcu.program_capacity_b
        
    assert length <= mcu.program_capacity_b, "Excessive length"
    
    logging.info("Reading %d bytes from %s...", length, mcu.name)
    data = [flasher.readProgramMemory(i) for i in range(length)]
    
    if fname is not None:
        logging.info("Saving binary data to \"%s\"...", fname)
        with open(fname, "wb") as fp:
            fp.write(bytes(data))
            
    if not quiet:
        page_size = mcu.page_size
        print("     | " + " ".join("%02X" % i for i in range(page_size)))
        print("-----|-" + "-" * (page_size * 3))
        for i in range(mcu.program_capacity_b // page_size):
            page = data[i * page_size : (i + 1) * page_size]
            if not page:
                break
            print((" %03X | " % (i * page_size)) + " ".join("%02X" % b for b in page))
    
def my_i8_bin(ival):
    sval = bin(ival)[2:]
    return ("0" * (8 - len(sval))) + sval
    
def dump_bits(flasher, fname, quiet):
    sig0 = flasher.readSignatureByte(0x00)
    sig1 = flasher.readSignatureByte(0x01)
    sig2 = flasher.readSignatureByte(0x02)
    
    calib0 = flasher.readCalibrationByte(0)
    calib1 = flasher.readCalibrationByte(1)
    
    lock = flasher.readLockBits()
    
    fuseL = flasher.readFuseByte(0)
    fuseH = flasher.readFuseByte(1)
    
    txt = """Signature:
0x000 : 0x%02X
0x001 : 0x%02X
0x002 : 0x%02X

Calibration(0, 1): 0x%02X 0x%02X
    
Lock bits: 0x%02X (0b%s)

Fuses (H, L): 0x%02X 0x%02X
  H: 0b%s
  L: 0b%s
""" % (sig0, sig1, sig2, calib0, calib1, lock, my_i8_bin(lock),
            fuseH, fuseL, my_i8_bin(fuseH), my_i8_bin(fuseL))
    
    if fname is not None:
        logging.info("Saving read summary to \"%s\"...", fname)
        with open(fname, "w") as fp:
            fp.write(txt)
            
    if not quiet:
        print(txt)

def interactive_fuse(flasher):
    print("Values of fuses now:")
    fuseL = flasher.readFuseByte(0)
    fuseH = flasher.readFuseByte(1)
    print(" H: 0x%02X (0b%s)" % (fuseH, my_i8_bin(fuseH)))
    print(" L: 0x%02X (0b%s)" % (fuseL, my_i8_bin(fuseL)))
    choice = ""
    try:
        while choice not in ("H", "L"):
            print("Enter fuse to modify ('H'/'L')")
            choice = input().strip().upper()
            
        while True:
            print("Specify new value of fuse")
            try:
                value = int(input(), base=0)
            except:
                print("Invalid format")
                continue
            print("Proceed to write value 0x%02X (0b%s) to fuse%s (y/n)?" % (
                    value, my_i8_bin(value), choice))
            
            if input().strip().lower() == 'y':
                break
                
        if choice == "H":
            flasher.writeFuseByte(1, value)
        else:
            flasher.writeFuseByte(0, value)
            
        print("Done.")
            
    except KeyboardInterrupt:
        print("Aborting")

def main(args):
    logging.getLogger().setLevel("INFO")
    
    if args.command == "list-mcus":
        list_mcus()
    
    else:
        mcu = get_mcu(args)
        mat = Klucha(mcu, args.low_speed)
        
        mat.enableProgramming()
        
        try:
                   
            if "write" == args.command:
                assert args.bin is not None, "Binary file must be specified"
                
                if not args.bin.endswith(".bin"):
                    logging.warning("File does not end with .bin extension. Might be incorrect format.")
                
                write_file(mat, args.bin, args.length)
                
            elif "read" == args.command:
                dump_flash(mat, args.output, args.length, args.quiet)
            
            elif "read-fuses-n-crap" == args.command:
                dump_bits(mat, args.output, args.quiet)
                
            elif "write-fuse" == args.command:
                interactive_fuse(mat)

        finally:
            mat.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AVR flasher")
    parser.add_argument("--mcu", help="Specify microcontroller model", default="attiny13")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--length", help="Length of read/write operation (in bytes)", type=int)
    parser.add_argument("--quiet", help="Don't print memory contents to console on read", action="store_true")
    parser.add_argument("--low_speed", help="Decrese speed of SPI clock", action="store_true")
    parser.add_argument("command", metavar="CMD", help="Command (nop | write | read | read-fuses-n-crap | write-fuse | list-mcus)",
            choices=["nop", "write", "read", "list-mcus", "read-fuses-n-crap", "write-fuse"])
    parser.add_argument("bin", metavar="BIN", help="Binary file", nargs="?")
    main(parser.parse_args())



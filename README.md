
# ATTINY Flasher on Raspberry Pi

Python script which allows to use Raspberry Pi as serial programmer of ATTINY microcontrollers (AVR).


## Raspberry Pi pinout 

```
                       __
               3.3  1 |..|
    RESET <--  GP2  3 |..|
                      |..| 6  GND
                      |..|
                      |..|
                      |..|
                      |..|
                      |..|
                      |..|
    <-- SPI0_MOSI  19 |..|
    --> SPI0_MISO  21 |..|
    --> SPI0_SCLK  23 |..|
                      |..|

```

## Serial programming - ATTINY13 


```
                _____ 
   \reset  1  -|o    |-  8  vcc  
              -|     |-  7  sck  
              -|     |-  6  miso 
      gnd  4  -|_____|-  5  mosi 
```


## Usage

```

kluchomat.py [-h] [--mcu MCU] [--output OUTPUT] [--length LENGTH] [--quiet] [--low_speed]
                    CMD [BIN]

AVR flasher

positional arguments:
  CMD              Command (nop | write | read | read-fuses-n-crap | write-fuse | list-mcus)
  BIN              Binary file

optional arguments:
  -h, --help       show this help message and exit
  --mcu MCU        Specify microcontroller model
  --output OUTPUT  Output file
  --length LENGTH  Length of read/write operation (in bytes)
  --quiet          Don't print memory contents to console on read
  --low_speed      Decrese speed of SPI clock

```

Script reads/writes program memory of microcontroller. It accepts raw binary (.bin) files as input data to write.
On write, it always starts at 0 offset and re-flashes entire program memory.

Commands:

 * nop - sends enable-programming command and quits - should be enough to check if connections to MCU are correct;
 * write - flashes program memory with code taken from .bin file; does chip-erase, programming and verifying;
 * read - reads contents of program memory; results are printed to console and/or output file;
 * read-fuses-n-crap - reads signature, lock bits, fuse bits and calibration bits and prints them;
 * write-fuse - writes fuse bits (interactive);
 * list-mcus - list possible values for --mcu option (supported models).

Important: use --low_speed option if your microcontroller is fused to run with slow clock speed (e.g. ATTINY13 with internal 128kHz osc).

## Limitations

This is a toy project. You probably should not use it.

 * Only ATTINY13 is supported - that is the one I needed to program when I wrote this. I might add other models later, but I probably won't.
 * No EEPROM access
 * No lock bits write command
 
 


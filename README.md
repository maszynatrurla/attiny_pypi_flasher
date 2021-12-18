
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

## Serial programming pinout 

(ATTINY13, ATTINY25, ATTINY45, ATTINY85)

```
                _____ 
   \reset  1  -|o    |-  8  vcc  
              -|     |-  7  sck  
              -|     |-  6  miso 
      gnd  4  -|_____|-  5  mosi 
```

(ATTINY2313, ATTINY4313)

```
                _____ 
   \reset  1  -|o    |-  20  vcc  
              -|     |-  19  sck  
              -|     |-  18  miso 
              -|     |-  17  mosi 
              -|     |-
              -|     |-
              -|     |-
              -|     |-
              -|     |-
     gnd  10  -|_____|-
```


## Usage

```

usage: kluchomat.py [-h] [--mcu MCU] [--output OUTPUT] [--length LENGTH] [--quiet] [--low_speed]
                    CMD [BIN]

AVR flasher

positional arguments:
  CMD              Command (nop | write | read | read-fuses-n-crap | write-fuse | list-mcus |
                   read-eeprom | write-eeprom)
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
 * read-eeprom - reads contents of EEPROM; results are printed to console and/or output file;
 * write-eeprom - writes contents of .bin file to EEPROM;
 * list-mcus - list possible values for --mcu option (supported models).

Important: use --low_speed option if your microcontroller is fused to run with slow clock speed (e.g. ATTINY13 with internal 128kHz osc).

## Limitations

This is a toy project. You probably should not use it.

 * List of supported microcontrollers is very limited and it is unlikely to grow;
 * I only really tested it with ATTINY13, ATTINY45 and ATTINY2313;
 * EEPROM write uses byte access, which is probably less efficient than page access;
 * No lock bits write command.
 


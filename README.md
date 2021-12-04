
= ATTINY Flasher on Raspberry Pi =

Python script which allows to use Raspberry Pi as serial programmer of ATTINY microcontrollers (AVR).


== Raspberry Pi pinout ==

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

== Serial programming - ATTINY13 ==


```
                _____ 
   \reset  1  -|o    |-  8  vcc  
              -|     |-  7  sck  
              -|     |-  6  miso 
      gnd  4  -|_____|-  5  mosi 
```


== Usage ==

```

kluchomat.py [-h] [--mcu MCU] [--output OUTPUT] [--length LENGTH] [--quiet] CMD [BIN]

AVR flasher

positional arguments:
  CMD              Command (nop | write | read | list-mcus)
  BIN              Binary file

optional arguments:
  -h, --help       show this help message and exit
  --mcu MCU        Specify microcontroller model
  --output OUTPUT  Output file
  --length LENGTH  Length of read/write operation (in bytes)
  --quiet          Don't print memory contents to console on read

```

Script reads/writes program memory of microcontroller. It accepts raw binary (.bin) files as input data to write.
On write, it always starts at 0 offset and re-programs entire program memory.


== Limitations ==

This is a toy project. You probably should not use it.

 * Only ATTINY13 is supported (that is the one I needed to program when I wrote this)
 * No EEPROM access
 * No fuse bits, lock bits or signature support
 
 


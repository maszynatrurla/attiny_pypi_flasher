# GPIO abstraction modoule for kluchomat
#
# This one uses RPi.GPIO module (python module for Rasperry Pi)
# but it can be replaced with something that uses more
# generic Linux approach to GPIOs, therefore making it run on
# something else than Raspberry Pi.

import RPi.GPIO as GP

def pin_init():
    """
    Initialize GPIO module.
    """
    GP.setmode(GP.BCM)
    GP.setwarnings(False)

class OutPin:
    def __init__(self, pno, initial = GP.HIGH):
        self._pno = pno
        GP.setup(channel=pno, direction=GP.OUT, initial=initial)
        
    def high(self):
        GP.output(self._pno, GP.HIGH)
        
    def low(self):
        GP.output(self._pno, GP.LOW)

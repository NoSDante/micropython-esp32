from machine import Pin, SDCard
from os import mount, umount, listdir

## SD-Card Modul ESP32 TTGO-T8 V1.7
# Slot 1 (mosi=15, sck=14, dat1=4, dat2=12)
# define Pins cs=13, miso=2

def mounting(slot=1, width=1, path="/sd", cs=13, miso=2, debug=False):
    if not isinstance(path, str): raise ValueError('SDCard path must be a string')
    # NOTE: prevent Thonny-ManagementError if path is empty
    if len(path) == 0: raise ValueError('SDCard path is empty')
    # NOTE: cannot mount SDCard, if path already exists
    if path.replace('/', '') in listdir():
        print("SDCard path '{}' exists in directory".format(path))
        return False
    print("\nmounting SDCard...")
    try:
        if debug: print('SDCard: slot={0}, Pins: cs={1}, miso={2}'.format(slot, cs, miso))
        """
        Note: Fix to mount SDCard with ESP32 TTGO-T8 V1.7
        pull up the Pins: cs, miso
        """
        pullup_pin([miso, cs])
        mount(SDCard(slot=slot, width=width, miso=Pin(miso), cs=Pin(cs)), path)
        print('SDCard mounted to path', path)
        return True
    except OSError as e:
        if debug: print('SDCard: errno', e)
        print("cannot mount SDCard")
        return False

def pullup_pin(pins):
    for pin in pins:
        Pin(pin).init(-1, Pin.PULL_UP)

from machine import Pin, SDCard
from os import mount, umount, listdir


## SD-Card Modul ESP32 TTGO-T8 V1.7
# Slot 2 (mosi=15, sck=14, miso=2)
# define Pin cs=13

def mounting(slot=1, width=1, path="/sd", mosi=15, miso=2, sck=14, cs=13, debug=False):
    if not isinstance(path, str): raise ValueError('SDCard path must be a string')
    # NOTE: prevent Thonny-ManagementError if path is empty
    if len(path) == 0: raise ValueError('SDCard path is empty')
    # NOTE: cannot mount SDCard, if path already exists
    if path.replace('/', '') in listdir():
        print("SDCard path '{}' exists in directory".format(path))
        return False
    print("\nmounting SDCard...")
    try:
        if debug: print('SDCard: slot={0}, Pins: mosi={1}, miso={2}, sck={3}, cs={4}'.format(slot, mosi, miso, sck, cs))
        #pullup_pin([cs])
        mount(SDCard(slot=slot, width=width, mosi=mosi, miso=miso, sck=sck, cs=cs), '/sd')
        print('SDCard mounted to path', path)
        return True
    except OSError as e:
        if debug: print('SDCard: errno', e)
        print("cannot mount SDCard")
        return False

def pullup_pin(pins):
    for pin in pins:
        Pin(pin).init(-1, Pin.PULL_UP)

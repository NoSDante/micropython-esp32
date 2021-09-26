from machine import Pin, SDCard, reset
import os

## SD-Card Modul ESP32 TTGO-T8 V1.7
# define Slot 1 (mosi=15, sck=14, dat1=4, dat2=12)
# define Pins cs=13, miso=2

def mount(slot=1, path="/sd", cs=13, miso=2, debug=False):
    if not isinstance(path, str): raise ValueError('SDCard path must be a string')
    # NOTE: Prevent Thonny ManagementError if path is empty
    if len(path) == 0: raise ValueError('SDCard path is empty')
    # NOTE: Cannot mount SDCard, if path already exists
    if path.replace('/', '') in os.listdir():
        print('SDCard path exists in directory', path)
        #print('eject SDCard...')
        #os.umount(path)
        return False
    print("mount SDCard...")
    try:
        if debug: print('SDCard: slot={0}, Pins: cs={1}, miso={2}'.format(slot, cs, miso))
        os.mount(SDCard(slot=slot, miso=Pin(miso), cs=Pin(cs)), path)
        print('SDCard mounted to path', path)
        return True
    except OSError as e:
        if debug: print('SDCard: errno', e)
        if e.args[0] == 16:
            if debug: print('SDCard: reset machine...')
            reset()
        print("cannot mount SDCard")
        return False

from core.sdcard import mounting
from machine import Pin

def pullup_pin(pins):
    for pin in pins:
        Pin(pin).init(-1, Pin.PULL_UP)

## SD-Card Modul ESP32 TTGO-T8 V1.7
# Slot 2 (mosi=15, sck=14, miso=2)
# define Pin cs=13

cs=13
#pullup_pin([cs])
mounting(slot=2, width=1, path="/sd", mosi=15, miso=2, sck=14, cs=cs, debug=False)

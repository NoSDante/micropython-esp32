# This file is executed on every boot (including wake-boot from deepsleep)
import os

# boot
print('boot...')

def no_debug():
    import esp
    esp.osdebug(None)
    
if not "boot.db" in os.listdir():
    print('setup...')
    try:
        from setup import setup
        setup()
    except Exception as e:
        raise Exception("setup failed", e)

#no_debug()

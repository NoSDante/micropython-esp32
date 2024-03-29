# tools

def scan_i2c_bus(i2c):
    devices = i2c.scan()
    print("\n--- I2C SCAN ---")
    if len(devices) == 0:
        print("No i2c device!")
    else:
        print('Devices found:',len(devices))
        for device in devices:
            print("Decimal address: ",device," | Hexa address: ",hex(device))
    return len(devices)
    
def scan_i2c_address(i2c, addrList=[]):
    devices = i2c.scan()
    print("\n--- I2C DEVICES ---")
    if len(devices) == 0:
        print("No i2c device!")
    else:
        for addr in addrList:
            if addr in devices:
                print("Device found! Hexa address: ",hex(addr))

def I2C_devices(i2c, addr=None):
    devices = i2c.scan()
    return(addr in devices)

# I2C CONFIG
I2C_SLOT = 1  # SDA=21, SCL=22
SDA_PIN  = 21
SCL_PIN  = 22

from machine import I2C, Pin

def I2C_Test():
    # i2c = I2C(I2C_SLOT, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
    i2c = I2C(I2C_SLOT)
    scan_i2c_bus(i2c)
    # SCD30=0x61, DS1307=0x68, BH1750=0x23, AS3539=0X01,0X02,0X03
    addrList = [0x61, 0x68, 0x23, 0X01, 0X02, 0X03] 
    scan_i2c_address(i2c, addrList=addrList)
    print(i2c_device(i2c, addr=0X01))

def settime_DS1307():
    from lib.ds1307 import DS1307
    ds1307 = DS1307(I2C(I2C_SLOT))
    from machine import RTC
    rtc = RTC()
    now = rtc.datetime() # get date and time
    ds1307.datetime(now)
    print(ds1307.datetime())

def I2C_AS3935():
    from time import sleep
    from lib.DFRobot_AS3935_Lib import DFRobot_AS3935
    i2c = I2C(I2C_SLOT)
    AS3935_I2C_ADDR = [0X01, 0X02, 0X03]
    for addr in AS3935_I2C_ADDR:
        print("initializing as3935 with I2C address", hex(addr))
        for retry in range(10):
            as3935 = DFRobot_AS3935(addr, i2c)
            if as3935.reset():
                break
            print("error initializing as3935", retry)
            sleep(0.5)

I2C_Test()
I2C_AS3935()
#settime_DS1307()
# helper
print('helper...')

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

def i2c_device(i2c, addr=None):
    devices = i2c.scan()
    return(addr in devices)


# I2C CONFIG
I2C_SLOT = 1  # SDA=21, SCL=22
SDA_PIN  = 21
SCL_PIN  = 22

# I2C TEST
from machine import I2C, Pin
#i2c = I2C(I2C_SLOT, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
i2c = I2C(I2C_SLOT)

print(scan_i2c_bus(i2c))
addrList = [0x61, 0x23, 0X01, 0X02, 0X03]  # SCD30=0x61, BH1750=0x23, AS3539=0X01,0X02,0X03
scan_i2c_address(i2c, addrList=addrList)
print(i2c_device(i2c, addr=0X01))

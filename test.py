import json
from os import remove

jsonobj = {
    "DEBUG"   : True,
    "TIMEZONE": {
        "UTC"     : 1,
        "ZONE"    : "MESZ - Mitteleuropäische Winterzeit (UTC+1)",
        "SUMMMER" : 3,
        "WINTER"  : 10
        }
    }

#jsonstr = "{'RTC': {'MODUL': 'DS1307'}, 'TIMEZONE': {'ZONE': 'MESZ - Mitteleurop\xe4ische Winterzeit (UTC+1)', 'SUMMMER': 3, 'WINTER': 10, 'UTC': 1}, 'NETWORK': {'DATABASE': '/network.db', 'AP': False, 'DEFAULT': 'default', 'RECONNECT': '7205', 'SMART': True, 'AP_IF': True, 'WIFI': True}, 'DEBUG': False, 'I2C': {'SDA': 21, 'SLOT': 1, 'FREQ': 400000, 'SCL': 22}, 'SDCARD': {'WIDTH': 1, 'SPI': 1, 'PATH': '/sd', 'MISO': 2, 'CS': 13}, 'DEVICE': {'PSRAM': '8MB', 'SDSLOT': 'Slot 1 mosi=15, sck=14, dat1=4, dat2=12', 'MODEL': 'TTGO T8 V1.7.1', 'FLASH': '4MB', 'BRAND': 'Tonysa', 'TYPE': 'ESP32-WROVER', 'SDCARD': 'Mount on SPI Slot 1', 'SDPINS': 'Pins cs=13, miso=2'}}"
#jsonstr = {'{"RTC":{"MODUL":"DS1307"},"I2C":{"FREQ":400000,"SLOT":1,"SCL":22,"SDA":21},"NETWORK":{"DATABASE":"/network.db","WIFI":true,"AP":false,"RECONNECT":7200,"SMART":true,"AP_IF":true,"DEFAULT":"default"},"DEBUG":false,"DEVICE":{"PSRAM":"8MB","SDCARD":"Mount on SPI Slot 1","MODEL":"TTGO T8 V1.7.1","SDSLOT":"Slot 1 mosi': '15, sck=14, dat1=4, dat2=12","SDPINS":"Pins cs=13, miso=2","TYPE":"ESP32-WROVER","FLASH":"4MB","BRAND":"Tonysa"},"SDCARD":{"CS":13,"SPI":1,"PATH":"/sd","MISO":2,"WIDTH":1},"TIMEZONE":{"UTC":1,"SUMMMER":3,"WINTER":10,"ZONE":"MESZ - Mitteleurop\xe4ische Winterzeit (UTC 1)"}}'}
jsonstr = {'RTC': {'MODUL': 'DS1307'}, 'I2C': {'FREQ': 400000, 'SLOT': 1, 'SCL': 22, 'SDA': 21}, 'NETWORK': {'DATABASE': '/network.db', 'WIFI': True, 'AP': True, 'RECONNECT': 7200, 'SMART': True, 'AP_IF': True, 'DEFAULT': 'default'}, 'DEBUG': False, 'DEVICE': {'PSRAM': '8MB', 'SDCARD': 'Mount on SPI Slot 1', 'MODEL': 'TTGO T8 V1.7.1', 'SDSLOT': 'Slot 1 mosi=15, sck=14, dat1=4, dat2=12', 'SDPINS': 'Pins cs=13, miso=2', 'TYPE': 'ESP32-WROVER', 'FLASH': '4MB', 'BRAND': 'Tonysa'}, 'SDCARD': {'PATH': '/sd', 'CS': 13, 'MOSI': 2, 'SPI': 1}, 'TIMEZONE': {'UTC': 1, 'SUMMMER': 3, 'WINTER': 10, 'ZONE': 'MESZ - Mitteleurop\xe4ische Winterzeit (UTC+1)'}}
print("POST-RAW:", jsonstr)
print("POST-LENGTH:", len(jsonstr))
print("POST-TYPE:", type(jsonstr))

data = jsonstr
data = str(data)
data = data.replace("'","\"")
data = data.replace("False","false")
data = data.replace("True","true")
#json_data = json.loads(jsonstr).encode("utf-8")
#data = json.dump(data).encode("utf-8")
print("STRING-CONVERTED:", data)

#jsonstr = str(jsonstr)
# my_json = jsonstr.encode('utf8').replace("'", '"')
# Load the JSON to a Python list & dump it back out as formatted JSON
# data = json.loads(my_json)
# s = json.dumps(data, indent=4, sort_keys=True)
# print(s)
print(data)
#data = data.encode("utf-8")
#data = json.dumps(data).encode("utf-8")
#print(data)
# with open('config/test.json', 'w+b') as file:
#     file.write(data)

with open('config/test.json', 'r') as file:
    json_data = json.load(file)
    print(json_data["DEBUG"])


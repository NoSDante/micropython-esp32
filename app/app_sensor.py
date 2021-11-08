from machine import Pin
from time import sleep, sleep_ms, localtime, mktime, ticks_ms, ticks_diff
import uasyncio as asyncio

# App libs
from app.database import Database
from app.store import Store
from app.display import Display
from app.lightstrip import Lightstrip
from app.sensors import Sensors, Scoring

# System controls
system = Database("/system.db")
debug = system.get("DEBUG")

# Store object is global
state = Store(
    reconnect = system.get("RECONNECT"),
    timesync = system.get("TIMESYNC"),
    sdcard = system.get("SDCARD"),
    wifi = system.get("WIFI"),
    connected = system.get("CONNECTED"),
    ap = system.get("AP"),
    ap_if = system.get("AP_IF")
)
app = Store(
    ready = False,
    nightmode = False,
    lightshow = 0
)
sensors = Store(
    scd30 = False,
    bh1750 = False,
    sps30 = False,
    as3935 = False,
    mq2 = False
)

# AS3935 loop
async def runWatchdogLightning(as3935, ligthstrip, interval=1):
    while 1:
        if as3935.trigger() == 0:
            if debug: print("[AS3935] Lightning detected")
            as3935.data = {
                "Lightning Distance": await as3935.getLightningDistKm(),
                "Strike Energy": await as3935.getStrikeEnergyRaw(),
                "time": time(),
                "date": date()
            }
            if debug: print("[AS3935]:", as3935.data)
            await ligthstrip.fade()
        await asyncio.sleep(interval)

# MQ2 loop
async def runWatchdogGas(mq2, interval=1):
    while mq2.trigger.value() == 0:
        await asyncio.sleep(2)
    if debug: print("[MQ2] heater finished")
    while 1:
        if mq2.trigger.value() == 0:
            if debug: print("[MQ2] gas or smoke detected")
            mq2.data = {
                "Smoke": mq2.readSmoke(),
                "LPG": mq2.readLPG(),
                "Methane": mq2.readMethane(),
                "Hydrogen": mq2.readHydrogen(),
                "date": date(),
                "time": time()
            }
            if debug: print("[MQ2]:", mq2.data)
        await asyncio.sleep(interval)

# BH1750 loop
async def runWatchdogLux(bh1750, interval=3):
    while 1:
        lux = await bh1750.luminance(bh1750.ONCE_HIRES_1)
        if lux:
            lux = round(lux,1)
            if len(bh1750.data) == 0:
                lux_max = lux_min = lux
            else:
                if lux > bh1750.data.get("lux_max"): lux_max = lux
                if lux < bh1750.data.get("lux_min"): lux_min = lux               
            bh1750.data = {
                'lux': lux,
                'lux_max': lux_max,
                'lux_min': lux_min,
                'time': time(),
                "date": date()
            }
        if debug: print('[BH1750] Illuminance: {} Lux'.format(bh1750.data["lux"]))
        await asyncio.sleep(interval)

# SCD30 loop
async def runWatchdogCO2(scd30, interval=2):
    if debug: err_read = 0
    while 1:
        try:
            while scd30.get_status_ready() != 1:
                await asyncio.sleep_ms(200)
            co2, temp, relh = scd30.read_measurement()
            co2  = int(co2)
            temp = round(temp, 1)
            relh = int(relh)
            if len(scd30.data) != 0:
                if co2 < scd30.data.get("co2_min") or co2_min == 0: co2_min = co2
                if co2 > scd30.data.get("co2_max"): co2_max = co2
                if temp < scd30.data.get("temp_min"): temp_min = temp
                if temp > scd30.data.get("temp_max"): temp_max = temp           
                if relh < scd30.data.get("relh_min"): relh_min = relh
                if relh > scd30.data.get("relh_max"): relh_max = relh
            else:
                co2_max  = co2_min = co2
                relh_max = relh_min = relh
                temp_max = temp_min = temp
            scd30.data = {
                'co2': co2,
                'co2_max': co2_max,
                'co2_min': co2_min,            
                'temp': temp,
                'temp_max': temp_max,
                'temp_min': temp_min,
                'relh': relh,
                'relh_max': relh_max,
                'relh_min': relh_min,
                'time': time(),
                "date": date()
                }
            if debug:
                print("[SCD30] CO2: {} ppm | Temp.: {:2.1f} °C | Hum.: {} % | akt.".format(co2, temp, relh))
                print("[SCD30] CO2: {} ppm | Temp.: {:2.1f} °C | Hum.: {} % | max.".format(co2_max, temp_max, relh_max))
                print("[SCD30] CO2: {} ppm | Temp.: {:2.1f} °C | Hum.: {} % | min.".format(co2_min, temp_min, relh_min))            
        except Exception as e:
            if debug:
                err_read += 1
                print("SCD30 read error! counts {}, {}".format(err_read, e))
            pass
    await asyncio.sleep(interval)
    
# SPS30 loop
async def runWatchdogDust(sps30, interval=2):
    if debug: err_read = 0
    while 1:
        try:
            data = sps30.get_measurement(debug=debug)            
            sps30.data = {
                'values': data,
                'time': time(),
                "date": date()
                }
            if debug: print("[SPS30]", data)
        except Exception as e:
            if debug:
                err_read += 1
                print("SPS30 read error! counts {}, {}".format(err_read, e))
            pass
    await asyncio.sleep(interval)

# Ready loop
async def waitfor_ready(interval=1):
    while not app.get('ready'):
        await asyncio.sleep(interval)

# helper
def time():
    t = localtime()
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])

def date():
    t = localtime()
    return "{:02d}.{:02d}.{}".format(t[2], t[1], t[0])

def date_as_int():
    t = localtime()
    return "{}{:02d}{:02d}".format(t[0], t[1], t[2])

def timestamp():
    return mktime(localtime())

def main():
   
    print("\nloading config...")
    
    # load app config
    config = Database("/app/app.db")

    # I2C
    I2C_SLOT = config.get("I2C").get("SLOT")
    SDA_PIN  = config.get("I2C").get("SDA")
    SCL_PIN  = config.get("I2C").get("SCL")
    
    # AS3935
    AS3935_INIT = config.get("AS3935").get("INIT")
    if AS3935_INIT:
        AS3935_IRQ_PIN     = config.get("AS3935").get("IRQ_PIN")
        AS3935_INDOOR      = config.get("AS3935").get("INDOOR")
        AS3935_DISTURBER   = config.get("AS3935").get("DISTURBER")
        AS3935_CAPACITANCE = config.get("AS3935").get("CAPACITANCE")
        AS3935_INTERVAL    = config.get("AS3935").get("INTERVAL")
    
    # MQ2
    MQ2_INIT = config.get("MQ2").get("INIT")
    if MQ2_INIT:
        MQ2_ANALOG_PIN  = config.get("MQ2").get("ANALOG_PIN")
        MQ2_DIGITAL_PIN = config.get("MQ2").get("DIGITAL_PIN")
        MQ2_INTERVAL    = config.get("MQ2").get("INTERVAL")
        MQ2_CALIBRATE   = config.get("MQ2").get("CALIBRATE")
        MQ2_BASEVOLTAGE = config.get("MQ2").get("BASEVOLTAGE")
    
    # SPS30
    SPS30_INIT = config.get("SPS30").get("INIT")             # use sensor
    if SPS30_INIT:
        SPS30_INTERVAL = config.get("SPS30").get("INTERVAL") # Loop async interval   
        SPS30_START    = config.get("SPS30").get("START")    # Start measurement
        SPS30_CLEAN    = config.get("SPS30").get("CLEAN")    # Clean fan
        SPS30_PORT     = config.get("SPS30").get("PORT")     # UART slot
        SPS30_RX       = config.get("SPS30").get("RX")       # RX Pin
        SPS30_TX       = config.get("SPS30").get("TX")       # TX Pin
        SPS30_SAMPLE   = config.get("SPS30").get("SAMPLE")   # default 1200
    
    # SCD30
    SCD30_INIT = config.get("SCD30").get("INIT")                       # use sensor
    if SCD30_INIT:
        SCD30_INTERVAL      = config.get("SCD30").get("INTERVAL")      # Loop async interval
        SCD30_MEAS_INTERVAL = config.get("SCD30").get("MEAS_INTERVAL") # default 2 for SCD30
        SCD30_AUTO_CALI     = config.get("SCD30").get("AUTO_CALI")     # Calibration auto
        SCD30_FORCED_CALI   = config.get("SCD30").get("FORCED_CALI")   # Calibration with a set value
        SCD30_FORCED_CO2    = config.get("SCD30").get("FORCED_CO2")    # Calibration value for forced calibration (min 400)
        SCD30_PAUSE         = config.get("SCD30").get("PAUSE")         # Delay for buffer receiving / default 1000
        SCD30_START         = config.get("SCD30").get("START")         # Start continous measurement
    
    # BH1750
    BH1750_INIT     = config.get("BH1750").get("INIT")
    BH1750_INTERVAL = config.get("BH1750").get("INTERVAL")
    
    # DISPLAY
    DISPLAY_INIT = config.get("DISPLAY").get("INIT")
    if DISPLAY_INIT:
        DISPLAY_INTERVAL = config.get("DISPLAY").get("INTERVAL")
        # TFT
        TFT_SPI   = config.get("TFT").get("SPI")
        TFT_MOSI  = config.get("TFT").get("MOSI")
        TFT_MISO  = config.get("TFT").get("MISO")
        TFT_SCK   = config.get("TFT").get("SCK")
        TFT_CS    = config.get("TFT").get("CS")
        TFT_DC    = config.get("TFT").get("DC")
        TFT_RESET = config.get("TFT").get("RESET")
        TFT_LED   = config.get("TFT").get("LED")
        if TFT_LED == False: TFT_LED = None
        # FONT
        FONT_FILE   = config.get("FONT").get("FILE")
        FONT_WIDTH  = config.get("FONT").get("WIDTH")
        FONT_HEIGHT = config.get("FONT").get("HEIGHT")
    
    # LIGHTSTRIP
    LIGHTSTRIP_INIT     = config.get("LIGHTSTRIP").get("INIT")     # use lightstrip
    LIGHTSTRIP_DATA_PIN = config.get("LIGHTSTRIP").get("DATA_PIN") # Data Pin
    LIGHTSTRIP_PIXEL    = config.get("LIGHTSTRIP").get("PIXEL")    # Number of pixels
    
    # NIGHTMODE FEATURE
    if config.get("NIGHTMODE").get("INIT"):
        app.set("nightmode", True)
        app.set("nightstart", config.get("NIGHTMODE").get("NIGHT_START"))
        app.set("nightend",   config.get("NIGHTMODE").get("NIGHT_END"))
    
    # LOGGER
    LOGGER_INIT = config.get("LOG").get("INIT")
    if LOGGER_INIT: LOGGER_CONFIG = config.get("LOG")
    
    del config
    
    # Lightstrip
    #lightstrip = Lightstrip(Pin(LIGHTSTRIP_DATA_PIN, Pin.OUT), pixel=LIGHTSTRIP_PIXEL)
    
    # Initializing I2C sensors
    sensor = Sensors(i2c=None, debug=debug)
    
    # SPS30
    if SPS30_INIT: sensor.init_SPS30(port=SPS30_PORT, rx=SPS30_RX, tx=SPS30_TX, start=SPS30_START, clean=SPS30_CLEAN, sample=SPS30_SAMPLE)
    
    print("\nloops...")
    
    # Async loops
    loop = asyncio.get_event_loop()
    
    # MQ2
#     if MQ2_INIT:
#         sensor.init_MQ2(
#             pin_analog=MQ2_ANALOG_PIN,
#             pin_trigger=Pin(MQ2_DIGITAL_PIN, Pin.IN),
#             baseVoltage=MQ2_BASEVOLTAGE,
#             calibrate=MQ2_CALIBRATE
#         )
    
    # BH1750
    #if BH1750_INIT: sensor.init_BH1750(i2c=None)
    
    # SCD30
    #if SCD30_INIT: sensor.init_SCD30(i2c=None, start=SCD30_START, pause=SCD30_PAUSE)
    
    
    # AS3935
#     if AS3935_INIT:
#         loop.create_task(sensor.init_AS3935(
#             i2c=None,
#             pin_irq=Pin(AS3935_IRQ_PIN, Pin.IN),
#             capacitance=AS3935_CAPACITANCE,
#             indoor=AS3935_INDOOR,
#             disturber=AS3935_DISTURBER
#         ))
    
    # Watchdog loops
    if hasattr(sensor, 'sps30'):
        sensors.set('sps30', True)
        loop.create_task(runWatchdogDust(sensor.sps30, interval=SPS30_INTERVAL))

    # Tasks loop forever
    loop.run_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')
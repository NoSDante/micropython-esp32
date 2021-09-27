from machine import Pin
from time import sleep, sleep_ms, localtime, mktime
import uasyncio as asyncio

# custom libs
from app.database import Database
from app.state import State
from app.display import Display
from app.lightstrip import Lightstrip
from app.sensors import Sensors, Scoring
from app.wifi import smart_connect, is_connected, get_ip

# system controls
system = Database("/system.db")
debug = system.get("DEBUG")

state = State(
    reconnect = system.get("RECONNECT"),
    timesync = system.get("TIMESYNC"),
    sdcard = system.get("SDCARD"),
    wifi = system.get("WIFI"),
    connected = system.get("CONNECTED"),
    ap = system.get("AP"),
    ready = False,
    lightshow = 0
)

# Lightstrip starter demo
async def runLightstripDemo(lightstrip):
    while state.get('ready') is not True:
        lightstrip.each( 1, color="DARK ORANGE", clear=False)
        await asyncio.sleep(0.5)
        lightstrip.clear()
        lightstrip.each( 2, color="DARK ORANGE", clear=False)
        await asyncio.sleep(0.5)
        lightstrip.clear()
    await lightstrip.bounce(color="GREEN")

# show system states
async def showSystemState(tft):
    
    state.set('ready', False)
    
    boot = Database("/boot.db")
    
    font_height = tft.font_height
    font_width = tft.font_width
    
    start_x = 5
    start_y = 5
    offset_y = 3
  
    # clearing stage
    tft.display.clear()
    coord_y = start_y
    line = 1
    
    # border
    tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color("WHITE"))
    # header device info
    text = "Device Info"
    center_x = (tft.display.width // 2) - (len(text)*font_width//3)
    
    tft.display.draw_rectangle(0, 0, tft.display.width, font_height+4, tft.color("WHITE"))
    tft.display.draw_text(center_x, coord_y-2, text, tft.font, tft.color("CYAN"))
    coord_y = start_y + font_height + 2
    line += 1
    # device info
    for key, value in boot.get("DEVICE").items():
        text = "{}: {}".format(key, value)
        tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("WHITE"))
        coord_y = start_y + (font_height*line) + offset_y
        line += 1  
    # progress bar
    rect_range = 3
    rect_height = 20
    rect_width = 310 // rect_range
    rect_x = 5
    rect_y = 215
    outer_width = (rect_width*rect_range) + rect_x-3
    tft.display.draw_rectangle(rect_x-1, rect_y-1, outer_width, rect_height+2, tft.color("WHITE"))
    for i in range(rect_range):
        tft.display.fill_rectangle(rect_x, rect_y, rect_width, rect_height, tft.color("GREEN"))
        rect_x = rect_x + rect_width
        await asyncio.sleep(1)
    await asyncio.sleep(1)
    
    # clearing stage
    tft.display.clear()
    coord_y = start_y
    line = 1
    
    # border
    tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color("WHITE"))    
    # header system info
    text = "System Status"
    center_x = (tft.display.width // 2) - (len(text)*font_width//4)
    tft.display.draw_rectangle(0, 0, tft.display.width, font_height+4, tft.color("WHITE"))
    tft.display.draw_text(center_x, coord_y-2, text, tft.font, tft.color("CYAN"))
    coord_y = start_y + font_height + 2
    line += 1    
    # text system info
    keys = system.keys() # global system
    for key in keys:
        value = system.get(key)
        text = "{}: {}".format(key, value)
        tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("WHITE"))
        coord_y = start_y + (font_height*line) + offset_y
        line += 1
    await asyncio.sleep(1)    
    # progress bar
    rect_height = 10
    rect_width = 31
    rect_x = 5
    rect_y = 225
    rect_range = 10
    outer_width = (rect_width*rect_range) + rect_x-3
    tft.display.draw_rectangle(rect_x-1, rect_y-1, outer_width, rect_height+2, tft.color("WHITE"))
    for i in range(rect_range):
        tft.display.fill_rectangle(rect_x, rect_y, rect_width, rect_height, tft.color("GREEN"))
        rect_x = rect_x + rect_width
        await asyncio.sleep(0.5)
    
    # del db object
    del boot
    
#     system.drop()
#     del system
    
    # ready for main loop
    state.set('ready', True)

# Counter loop
async def runCounter(interval=1):
    counter = 0
    while True:
        counter += 1
        print('[LOOP] Counter:', counter)
        await asyncio.sleep(interval)

# Network reconnecting loop
async def runReconnect(interval=3600):
    while state.get('reconnect') > 0:
        await asyncio.sleep(interval)
        if debug: print('network' , end=' ')
        if state.get('wifi') and not is_connected():
            print('reconnecting...')
            smart_connect()
            if is_connected():
                state.set("connected", True)
                state.set("ip_address", get_ip())
                interval = state.get('reconnect')
                if state.get('timesync') is not True:
                    from ntptime import settime
                    from timezone import Timezone
                    timezone = boot.get("TIMEZONE")
                    utc = timezone.get("UTC")
                    if debug: print("TIMEZONE:", timezone.get("ZONE"))
                    settime()
                    Timezone(utc).offset()                    
                    state.set('timesync', True)
                    if debug: print('Time synchronized')
            else:
                state.set("connected", False)
                state.set("ip_address", "0.0.0.0")
                interval = 900
        else:
            if debug: print('connected')
            state.set("connected", True)

# AS3935 loop
async def runWatchdogLightning(as3935, ligthstrip, interval=1):
    while True:
        if as3935.trigger() == 0:
            if debug: print("[AS3935] Lightning detected")
            as3935.data = {
                "Lightning Distance": await as3935.getLightningDistKm(),
                "Strike Energy": await as3935.getStrikeEnergyRaw(),
                "time": time()
            }
            if debug: print("[AS3935]:", as3935.data)
            await ligthstrip.fade()
        await asyncio.sleep(interval)

# MQ2 loop
async def runWatchdogGas(mq2, ligthstrip, interval=1):
    while mq2.trigger.value() == 0:
        await asyncio.sleep(2)
    if debug: print("[MQ2] heater finished")
        
    while True:
        if mq2.trigger.value() == 0:
            if debug: print("[MQ2] gas detected")
            mq2.data = {
                "Smoke": mq2.readSmoke(),
                "LPG": mq2.readLPG(),
                "Methane": mq2.readMethane(),
                "Hydrogen": mq2.readHydrogen(),
                "time": time()
            }
            await ligthstrip.fade()
            if debug: print("[MQ2]:", mq2.data)
        await asyncio.sleep(interval)

# BH1750 loop
async def runWatchdogLux(bh1750, interval=3):
    while True:
        lux = await bh1750.luminance(bh1750.ONCE_HIRES_1)
        lux = round(lux,1)
        if len(bh1750.data) != 0:
            if lux > bh1750.data.get("lux_max"): lux_max = lux
            if lux < bh1750.data.get("lux_min"): lux_min = lux   
        else:
            lux_max = lux_min = lux
        bh1750.data = {
            'lux': lux,
            'lux_max': lux_max,
            'lux_min': lux_min,
            'time': time()
        }
        if debug: print('[BH1750] Illuminance: {} Lux'.format(bh1750.data["lux"]))
        await asyncio.sleep(interval)

# SCD30 loop
async def runWatchdogCO2(scd30, interval=2):
    if debug: err_read = 0
    while True:
        try:
            while scd30.get_status_ready() != 1:
                await asyncio.sleep_ms(200)
            co2, temperature, relh = scd30.read_measurement()
            co2 = int(co2)
            temperature = round(temperature, 1)
            relh = int(relh)
            if len(scd30.data) != 0:
                if co2 < scd30.data.get("co2_min") or co2_min == 0: co2_min = co2
                if co2 > scd30.data.get("co2_max"): co2_max = co2
                if temperature < scd30.data.get("temperature_min"): temperature_min = temperature
                if temperature > scd30.data.get("temperature_max"): temperature_max = temperature                
                if relh < scd30.data.get("relh_min"): relh_min = relh
                if relh > scd30.data.get("relh_max"): relh_max = relh   
            else:
                co2_max = co2_min = co2
                relh_max = relh_min = relh
                temperature_max = temperature_min = temperature
            scd30.data = {
                'co2': co2,
                'co2_max': co2_max,
                'co2_min': co2_min,            
                'temperature': temperature,
                'temperature_max': temperature_max,
                'temperature_min': temperature_min,
                'relh': relh,
                'relh_max': relh_max,
                'relh_min': relh_min,
                'time': time()
                }
            if debug:
                print("[SCD30] akt. CO2: {} ppm | act. Temperatur: {:2f} °C | akt. Feuchtigkeit: {} %".format(co2, temperature, relh))
                print("[SCD30] max. CO2: {} ppm | max. Temperatur: {:2f} °C | max. Feuchtigkeit: {} %".format(co2_max, temperature_max, relh_max))
                print("[SCD30] min. CO2: {} ppm | min. Temperatur: {:2f} °C | min. Feuchtigkeit: {} %".format(co2_min, temperature_min, relh_min))            
        except Exception as e:
            if debug:
                err_read += 1
                print("SCD30 read error! counts {}, {}".format(err_read, e))
            pass
    await asyncio.sleep(interval)
    
# SPS30 loop
async def runWatchdogDust(sps30, interval=2):
    if debug: err_read = 0
    while True:
        try:
            data = sps30.read_measurement(debug=debug)
            sps30.data = data
            print("[SPS30]", data)
        except Exception as e:
            if debug:
                err_read += 1
                print("SPS30 read error! counts {}, {}").format(err_read, e)
            pass
    await asyncio.sleep(interval)


# Main loop
async def showSensorData(tft, sensor, interval=2):
    
    progress_wait = 2
    font_height = tft.font_height
    font_width = tft.font_width
    
    # color setting
    background_color = "BLACK"
    border_color = "WHITE"
    header_color = "CYAN"
    item_color = "WHITE"
    value_color = "CYAN"
    
    # clear
    tft.display.clear()
    
    # border
    tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color(border_color))
    
    # start coords
    start_x = 5
    start_y = 5
    offset_y = 5
    
    # first line header
    line = 1
    coord_y = start_y
    
    # header
    text = "Sensors"
    #today = date()
    now = time()
    
    #tft.display.draw_text(start_x, coord_y, today, tft.font, tft.color("YELLOW"))
    tft.display.draw_text(start_x, coord_y, now[0:5], tft.font, tft.color("YELLOW"))
    center_x = (tft.display.width//2) - (((len(text)*font_width))//4)
    tft.display.draw_rectangle(0, 0, tft.display.width, font_height+4, tft.color("WHITE"))
    tft.display.draw_text(center_x, coord_y-2, text, tft.font, tft.color(header_color))
    # next line
    coord_y = start_y + (font_height*line) + offset_y - 2
    line += 1
    
    items = [
        "CO2",
        "Temp.",
        "Feucht.",
        "Licht."
        ]
    
    offset_x = len(max(items, key=len))*(font_width-(font_width//4)) + start_x
    #print(offset_x)
    #offset_x = 110 + start_x

    for i in range (len(items)):
        text = items[i]
        tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color(item_color))
        # next line
        coord_y = start_y + (font_height*line) + offset_y - 2 
        line += 1
        tft.display.draw_hline(0, coord_y-1, tft.display.width-start_x, tft.color(item_color))

    mq2_counter = 0
    scoring = Scoring()
    
    while True:
        #if debug: print('MQ2:', sensor.mq2.data)
        #if debug: print('BH1750:', sensor.bh1750.data)
        #if debug: print('SCD30:', sensor.scd30.data)
        #if debug: print('[SPS30]', sensor.sps30.data)
        
        # reset y-coords
        line = 1
        coord_y = start_y
            
        # up to date
#         if today != date():
#             today = date()
#             tft.display.fill_rectangle(start_x, coord_y, (font_width*len(today)), font_height, tft.color("BLACK"))
#             tft.display.draw_text(start_x, coord_y, today, tft.font, tft.color("YELLOW"))
#         coord_y = start_y + (font_height*line) + offset_y
#         line += 1
        
        # time update
        if now[3:5] != time()[3:5]:
            now = time()
            tft.display.fill_rectangle(start_x, coord_y-2, (font_width*len(now[0:5])), font_height, tft.color("BLACK"))
            tft.display.draw_text(start_x, coord_y-2, now[0:5], tft.font, tft.color("YELLOW"))
        coord_y = start_y + (font_height*line) + offset_y
        line += 1
        
        # x-coord for value, scoring
        coord_x = offset_x
        clear_width = tft.display.width - start_x - coord_x + offset_y

        # CO2 data, scoring
        co2  = sensor.scd30.data.get("co2")
        # scoring
        score = scoring.co2(co2)
        color = scoring.color(score)
        value = "{} ppm".format(co2)
        # clear area
        tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color("BLACK"))
        # show value
        tft.display.draw_text(coord_x, coord_y-2, value, tft.font, tft.color(value_color))
        # show scoring
        #right_x = coord_x + (len(value)*(font_width)//3) - start_x
        right_x = 220
        tft.display.draw_text(right_x, coord_y, score, tft.font, tft.color(color))       
        # next line
        coord_y = start_y + (font_height*line) + offset_y
        line += 1
        
        # Temperature, Humidity data
        temp  = sensor.scd30.data.get("temperature")
        hum = sensor.scd30.data.get("relh")
        # scoring
        hi, score = scoring.heatindex(temp, hum)
        color = scoring.color(score)
        value = "{} C".format(str(temp).replace(".", ","))
        # clear area
        tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color("BLACK"))
        # show value
        tft.display.draw_text(coord_x, coord_y-2, value, tft.font, tft.color(value_color))
        # show scoring
        #right_x = start_x + coord_x + (len(value)*(font_width-font_width//3))
        tft.display.draw_text(right_x, coord_y, score, tft.font, tft.color(color))       
        # next line
        coord_y = start_y + (font_height*line) + offset_y
        line += 1
        
        # Humidity scoring
        score = scoring.humidity(hum)
        color = scoring.color(score)
        value = "{} %".format(str(hum))
        # clear area
        tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color("BLACK"))
        # show value
        tft.display.draw_text(coord_x, coord_y-2, value, tft.font, tft.color(value_color))
        # show scoring
#        #right_x = start_x + coord_x + (len(value)*(font_width-font_width//3))
        tft.display.draw_text(right_x, coord_y, score, tft.font, tft.color(color))       
        # next line
        coord_y = start_y + (font_height*line) + offset_y
        line += 1
        
        # Lux
        value = "{} lux".format(str(sensor.bh1750.data.get("lux")).replace(".", ","))
        tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color("BLACK"))
        # show value
        tft.display.draw_text(coord_x, coord_y-2, value, tft.font, tft.color(value_color))
        # next line
        coord_y = start_y + (font_height*line) + offset_y
        line += 1
    
        if sensor.mq2.data:
            data = sensor.mq2.data
            # draw text
#             for key, value in data.items():          
#                 text = "{} {}".format(key, str(value))
#                 tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("WHITE"))
#                 coord_y = start_y + (font_height*line) + offset_y
#                 line += 1
            mq2_counter += 1
            text = "Gas"
            tft.display.draw_text(270, 180, text , tft.font, tft.color("RED"))
            if mq2_counter >= 2:
                sensor.mq2.data = {}
                mq2_counter = 0
                tft.display.draw_rectangle(270, 180, (font_width*len(text)), font_height, tft.color("BLACK"))
       
        if interval >= progress_wait:
            interval = interval - progress_wait        
        await asyncio.sleep(interval)

        # progress bar
        rect_range = 3
        rect_height = 20
        rect_width = 310 // rect_range
        rect_x = 5
        rect_y = 215
        outer_width = (rect_width*rect_range) + rect_x-3
        tft.display.draw_rectangle(rect_x-1, rect_y-1, outer_width, rect_height+2, tft.color("WHITE"))
        for i in range(rect_range):
            tft.display.fill_rectangle(rect_x, rect_y, rect_width, rect_height, tft.color("GREEN"))
            rect_x = rect_x + rect_width
            await asyncio.sleep(0.5)
        tft.display.fill_rectangle(4, 214, outer_width, rect_height+2, tft.color("BLACK"))
        await asyncio.sleep(0.1)

def waitfor_ready(interval=1):
    while state.get('ready') is not True:
        await asyncio.sleep(interval)
        
def wait(sec):
    await asyncio.sleep(sec)
        
# HELPER
def time():
    t = localtime()
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])

def date():
    t = localtime()
    return "{:02d}.{:02d}.{}".format(t[2], t[1], t[0])

def timestamp():
    return mktime(localtime())


# Main
def main():
    
    ##
    # TODO: load config
    ##
    
    # I2C
    I2C_SLOT = 1
    SDA_PIN  = 21
    SCL_PIN  = 22

    # AS3935
    AS3935_IRQ = 35
    AS3935_INDOOR = True
    AS3935_DISTURBER = True
    AS3935_CAPACITANCE = 120
    AS3935_INTERVAL = 1

    # MQ2
    MQ2_ANALOG = 34
    MQ2_DIGITAL = 0
    MQ2_INTERVAL = 1
    MQ2_CALIBRATE = False
    MQ2_BASEVOLTAGE = 5.0

    # BUZZER
    #BUZZER_PIN = 27
    #buzzer = Pin(BUZZER_PIN, Pin.OUT, value=0)

    # LIGHTSTRIP
    LIGHTSTRIP_DATA = 27     # Data Pin
    LIGHTSTRIP_PIXEL = 8     # Number of Pixels

    # SPS30
    SPS30_INTERVAL = 2       # Loop async interval
    SPS30_UART = 2           # UART Slot
    SPS30_RX = 32            # RX Pin
    SPS30_TX = 33            # TX Pin
    SPS30_SAMPLE = 0         # default 1200
    SPS30_START = True       # Start

    # SCD30
    SCD30_INTERVAL = 2        # Loop async interval
    SCD30_MEAS_INTERVAL = 2   # default 2 for SCD30
    SCD30_AUTO_CALI = False   # Calibration auto
    SCD30_FORCED_CALI = False # Calibration with a set value
    SCD30_FORCED_CO2 = 400    # Calibration value for forced calibration (min 400)
    SCD30_PAUSE = 2000        # Delay for buffer receiving / default 1000
    SCD30_START = True        # Start continous measurement

    # BH1750
    BH1750_INTERVAL = 2

    # TFT
    TFT_SPI = 2
    TFT_MOSI = 23
    TFT_MISO = 19
    TFT_SCK  = 18
    TFT_CS = 5
    TFT_DC = 26
    TFT_RESET = 25
    TFT_LED = None

    # DISPLAY
    DISPLAY_INTERVAL = 3

    # FONT
    #FONT_FILE = 'tft\fonts\Espresso_Dolce18x24.c'
    FONT_FILE = 'Espresso_Dolce18x24.c'
    FONT_WIDTH = 18
    FONT_HEIGHT = 24
    
    print("display initializing...")
    
    # DISPLAY
    tft = Display(cs=TFT_CS, dc=TFT_DC, reset=TFT_RESET, width=320, height=240, rotation=90)
    #tft = Display(cs=TFT_CS, dc=TFT_DC, reset=TFT_RESET, width=240, height=320, rotation=0)
    tft.setFont(FONT_FILE, FONT_WIDTH, FONT_HEIGHT)
    
    font_height = tft.font_height
    font_width = tft.font_width
    
    start_x = tft.display.width // 4
    start_y = tft.display.height // 6
    coord_y = start_y
    offset_y = 4
    line = 1
    
    if debug:
        text = "DEBUG MODUS"
        color= "YELLOW"
    else:
        text = "Air Quality Monitoring"
        color= "LIME"
    
    print(text)
    tft.display.draw_text(5, 10, text, tft.font, tft.color(color))

    # border
    tft.display.draw_rectangle(start_x-offset_y, start_y-offset_y, tft.display.width-120, tft.display.height-60, tft.color("WHITE"))    

    text = "display initialized"
    print(text)
    tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("GREEN"))

    text = "initializing..."
    print(text)
    coord_y = start_y + (font_height*line) + offset_y
    line += 1
    tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("CYAN"))
    
    text = "lightstrip"
    print(text)
    coord_y = start_y + (font_height*line) + offset_y
    line += 1
    tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("WHITE"))
    
    # lightstrip
    lightstrip = Lightstrip(Pin(LIGHTSTRIP_DATA, Pin.OUT), pixel=LIGHTSTRIP_PIXEL)
    
    text = "sensors"
    print(text)
    coord_y = start_y + (font_height*line) + offset_y
    line += 1
    tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("WHITE"))
    
    # Sensors
    sensor = Sensors(i2c=None, debug=debug)
    
    # BH1750
    sensor.init_BH1750(i2c=None)
    
    # MQ2
    sensor.init_MQ2(
        pin_analog=MQ2_ANALOG,
        pin_trigger=Pin(MQ2_DIGITAL, Pin.IN),
        baseVoltage=MQ2_BASEVOLTAGE,
        calibrate=MQ2_CALIBRATE
    )
    
    # SCD30
    sensor.init_SCD30(i2c=None, start=SCD30_START, pause=SCD30_PAUSE)
    #sensor.scd30.soft_reset()
    
    # SPS30
    #sensor.init_SPS30(slot=SPS30_UART, rx=SPS30_RX, tx=SPS30_TX, sample=SPS30_SAMPLE)
    
    text = "application..."
    print(text)
    coord_y = start_y + (font_height*line) + offset_y
    line += 1    
    tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("CYAN"))
    
#     text = "web"
#     print(text)
#     coord_y = start_y + (font_height*line) + offset_y
#     line += 1    
#     tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("WHITE"))
    
    text = "loops"
    print(text)
    coord_y = start_y + (font_height*line) + offset_y
    line += 1    
    tft.display.draw_text(start_x, coord_y, text, tft.font, tft.color("WHITE"))
    
    del text
    del color
    
    # small progress bar
    rect_height = 10
    rect_width = 103
    rect_x = 5
    rect_y = 225
    rect_range = 3
    outer_width = (rect_width*rect_range) + rect_x-3
    tft.display.draw_rectangle(rect_x-1, rect_y-1, outer_width, rect_height+2, tft.color("WHITE"))
    for i in range(rect_range):
        tft.display.fill_rectangle(rect_x, rect_y, rect_width, rect_height, tft.color("GREEN"))
        rect_x = rect_x + rect_width
        sleep(0.4)
    
    # async loops
    loop = asyncio.get_event_loop()
    
    # lightstrip demo
    loop.create_task(runLightstripDemo(lightstrip))
  
    # AS3935
    loop.create_task(sensor.init_AS3935(
        i2c=None,
        pin_irq=Pin(AS3935_IRQ, Pin.IN),
        capacitance=AS3935_CAPACITANCE,
        indoor=AS3935_INDOOR,
        disturber=AS3935_DISTURBER
    ))
        
    # show system status
    if debug:
        loop.create_task(showSystemState(tft))
    else:
        state.set('ready', True)
    
    # Watchdog loops
    if sensor.mq2:    loop.create_task(runWatchdogGas(sensor.mq2, lightstrip, interval=MQ2_INTERVAL))
    if sensor.bh1750: loop.create_task(runWatchdogLux(sensor.bh1750, interval=BH1750_INTERVAL))
    if sensor.scd30:  loop.create_task(runWatchdogCO2(sensor.scd30, interval=SCD30_INTERVAL))
    #if sensor.sps30:  loop.create_task(runWatchdogDust(sensor.sps30, interval=SPS30_INTERVAL))
    #if sensor.as3935: loop.create_task(runWatchdogLightning(sensor.as3935, lightstrip, interval=AS3935_INTERVAL))
    
    loop.create_task(runCounter(interval=1))
    
    # WIFI reconnecting
    reconnect = state.get('reconnect')
    if reconnect > 0:
        loop.create_task(runReconnect(interval=reconnect))
    
    # Wait for state ready
    loop.run_until_complete(waitfor_ready())
    
    # Main loop
    loop.create_task(showSensorData(tft, sensor, interval=DISPLAY_INTERVAL))
    loop.run_forever()


if __name__ == '__main__': 
    try:
        main()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')


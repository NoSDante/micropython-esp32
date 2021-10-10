from machine import Pin
from time import sleep, sleep_ms, localtime, mktime, ticks_ms, ticks_diff
import uasyncio as asyncio

# custom libs
from app.database import Database
from app.state import State
from app.display import Display
from app.lightstrip import Lightstrip
from app.sensors import Sensors, Scoring

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
    
    START_X = 5
    START_Y = 5
    offset_y = 3
  
    # clearing stage
    tft.display.clear()
    coord_y = START_Y
    line = 1
    
    # border
    tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color("WHITE"))
    # header device info
    text = "Device Info"
    center_x = (tft.display.width // 2) - (len(text)*font_width//3)
    
    tft.display.draw_rectangle(0, 0, tft.display.width, font_height+4, tft.color("WHITE"))
    tft.display.draw_text(center_x, coord_y-2, text, tft.font, tft.color("CYAN"))
    coord_y = START_Y + font_height + 2
    line += 1
    # device info
    for key, value in boot.get("DEVICE").items():
        text = "{}: {}".format(key, value)
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("WHITE"))
        coord_y = START_Y + (font_height*line) + offset_y
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
    coord_y = START_Y
    line = 1
    
    # border
    tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color("WHITE"))    
    # header system info
    text = "System Status"
    center_x = (tft.display.width // 2) - (len(text)*font_width//4)
    tft.display.draw_rectangle(0, 0, tft.display.width, font_height+4, tft.color("WHITE"))
    tft.display.draw_text(center_x, coord_y-2, text, tft.font, tft.color("CYAN"))
    coord_y = START_Y + font_height + 2
    line += 1    
    # text system info
    keys = system.keys() # global system
    for key in keys:
        value = system.get(key)
        text = "{}: {}".format(key, value)
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("WHITE"))
        coord_y = START_Y + (font_height*line) + offset_y
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
    
    # del database object
    del boot
    
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
    from wifi import smart_connect, is_connected, get_ip
    while state.get('reconnect') > 0:
        await asyncio.sleep(interval)
        if debug: print('network' , end=' ')
        if state.get('wifi') and not is_connected():
            print('reconnecting...')
            smart_connect()
            #connect()
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

# AS3935 loop
async def runWatchdogLightning(as3935, ligthstrip, interval=1):
    while True:
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
                "date": date(),
                "time": time()
            }
            await ligthstrip.fade()
            if debug: print("[MQ2]:", mq2.data)
        await asyncio.sleep(interval)

# BH1750 loop
async def runWatchdogLux(bh1750, interval=3):
    while True:
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
    while True:
        try:
            while scd30.get_status_ready() != 1:
                await asyncio.sleep_ms(200)
            co2, temp, relh = scd30.read_measurement()
            co2 = int(co2)
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
                co2_max = co2_min = co2
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
    while True:
        try:
            data = sps30.read_measurement(debug=debug)            
            sps30.data = {
                'values': data,
                'time': time(),
                "date": date()
                }
            if debug: print("[SPS30]", data)
        except Exception as e:
            if debug:
                err_read += 1
                print("SPS30 read error! counts {}, {}").format(err_read, e)
            pass
    await asyncio.sleep(interval)


# Main loop
async def showSensorData(tft, sensor, lightstrip, interval=2):
    
    await asyncio.sleep(5)
    
    # font width, heigt for calculating coords
    font_height = tft.font_height
    font_width = tft.font_width
    
    # color setting
    CLEAR_COLOR  = "BLACK"
    BORDER_COLOR = "WHITE"
    HEADER_COLOR = "BLUE"
    ITEM_COLOR   = "WHITE"
    LINE_COLOR   = "WHITE"
    VALUE_COLOR  = "CYAN"
    CLOCK_COLOR  = "YELLOW"

    # clearing
    tft.display.clear()
    
    # page border
    tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color(BORDER_COLOR))
    
    # const 1px border
    BORDER_Y = 1
    BORDER_X = 1
    
    # adjustable coords
    offset_y = 2
    offset_x = 6
    
    # start coords draw text
    START_X = BORDER_X + offset_x
    START_Y = BORDER_Y + offset_y
    
    """
    NOTE: x-coords need to be static values
    it's not possible to calculate usefull coordinates with length of string * font-width
    the declacred font-width seems to be the max-width of a letter
    letters need a different size of pixels - M an I for example
    """
    coord_x1 = 90
    coord_x2 = 210
    co2_coord_x2 = 210
    netstate_coord_x = 275
    
    # time for clock
    now = time()
    today = date()
    
    """
    1. line header
    """
    # draw time
    text = now[0:5]
    tft.display.draw_text(START_X, START_Y, text, tft.font, tft.color(CLOCK_COLOR))
    # draw heading
    text = "ENVIRONMENT"
    tft.display.draw_text(coord_x1, START_Y, text, tft.font, tft.color(HEADER_COLOR)) 
    # draw line
    coord_y = START_Y + font_height
    tft.display.draw_hline(0, coord_y, tft.display.width, tft.color(LINE_COLOR))
    # coord vertical line
    vline_y = coord_y
    
    # sensor state
    scd30  = False
    sps30  = False 
    bh1750 = False
    mq2    = False
    
    # set mectrics for definded sensor
    # order by line drawing
    metric = []
    
    if hasattr(sensor, 'scd30'):
        scd30 = True
        # define metrics
        metric.append('CO2')
        metric.append('Temp.')
        metric.append('Hum.')
        # init sensor values
        CO2_WARNING_VALUE = 800        
        co2_last = None
        co2_max_last = None
        co2_min_last = None
        co2_warning = None
        co2_warning_last = None
        temp_last = None
        temp_max_last = None
        temp_min_last = None
    if hasattr(sensor, 'sps30'):
        sps30 = True
        # define metrics
        #
    if hasattr(sensor, 'bh1750'):
        bh1750 = True
        # define metric        
        metric.append('Light.')
         # init values
        hum_last  = None
        lux_last  = None
    if hasattr(sensor, 'mq2'):
        mq2 = True
        # init values
        mq2_counter = 0         
    
    # draw metrics and lines
    for i in range (len(metric)):
        coord_y += START_Y       
        text = metric[i]
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color(ITEM_COLOR))
        # draw horizontal line
        coord_y += font_height + offset_y
        tft.display.draw_hline(0, coord_y, tft.display.width, tft.color(LINE_COLOR))
    # draw vertical lines
    tft.display.draw_vline(coord_x1-offset_x, vline_y, coord_y-START_Y-font_height, tft.color(LINE_COLOR))
    #tft.display.draw_vline(coord_x2-offset_x, vline_y, coord_y-START_Y-font_height, tft.color(LINE_COLOR))
    
    # score sensor values
    scoring = Scoring()
    
    while True:
         
        # calcaulate interval
        start_time = ticks_ms() # get millisecond counter
        
        """
        1. line header
        update clocktime
        update network state
        """
        if now[3:5] != time()[3:5]:
            now = time()
            tft.display.fill_rectangle(START_X, START_Y, coord_x1-offset_x, font_height, tft.color(CLEAR_COLOR))
            tft.display.draw_text(START_X, START_Y, now[0:5], tft.font, tft.color(CLOCK_COLOR))
        color = "GREEN"
        if state.get('wifi'):
            text = "WIFI"
            if not state.get('connected'): color = "DARK ORANGE"
        if state.get('ap'):
            text = "AP"
        tft.display.fill_rectangle(netstate_coord_x, START_Y, tft.display.width-netstate_coord_x-offset_x, font_height, tft.color(CLEAR_COLOR))
        tft.display.draw_text(netstate_coord_x, START_Y, text, tft.font, tft.color(color))
        
        """
        NOTE:
        reset coord-y to draw first value (after headline)
        set x-coord for sensor values (next to metrics)
        set clearing space for values
        """
        coord_y = START_Y + font_height + offset_y
        coord_x = coord_x1
        clear_width = tft.display.width - START_X - coord_x + offset_x

        """
        2. line CO2
        scoring value
        """
        co2  = sensor.scd30.data.get("co2")
        if co2_last != co2:
            # scoring
            score = scoring.co2(co2)
            color = scoring.color(score)
            value = "{} ppm".format(co2)
            if co2 >= CO2_WARNING_VALUE:
                co2_warning = "CO2 score is {}".format(score)
                co2_score_color = color
            else:
                co2_score_color = VALUE_COLOR
                co2_warning = None
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            tft.display.fill_rectangle(coord_x2, coord_y-offset_y+BORDER_Y, tft.display.width-coord_x2-BORDER_X, font_height+START_Y+BORDER_Y, tft.color(CLEAR_COLOR))            
            # draw value
            tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color(co2_score_color))
            # draw scoring
            tft.display.fill_rectangle(coord_x2, coord_y-offset_y+BORDER_Y, tft.display.width-coord_x2-BORDER_X, font_height+START_Y+BORDER_Y, tft.color(color))
            # save as last value
            co2_last = co2
        
        """
        3. line Temperature
        scoring heatindex
        """
        # get values
        temp  = sensor.scd30.data.get("temp")
        hum = sensor.scd30.data.get("relh")
        # next draw coord
        coord_y += font_height + offset_y + START_Y        
        if temp_last != temp:
            # scoring
            value = "{} C".format(str(temp).replace(".", ","))
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            # draw value
            tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color(VALUE_COLOR))
            # scoring heatindex or temperature
            hi, score = scoring.heatindex(temp, hum)
            if hi:
                color = scoring.color(score)
            else:
                score = scoring.temperature(temp)
                color = scoring.color(score)
            # draw scoring
            tft.display.draw_text(coord_x2, coord_y, score, tft.font, tft.color(color))  
            # save as last value
            temp_last = temp
        
        """
        4. line Humidity
        no scoring
        """
        # next draw coord
        coord_y += font_height + offset_y + START_Y
        if hum_last != hum:
            score = scoring.humidity(hum)
            color = scoring.color(score)
            value = "{} %".format(str(hum))
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            # draw value
            tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color(VALUE_COLOR))
            # draw scoring
            tft.display.draw_text(coord_x2, coord_y, score, tft.font, tft.color(color))       
            # save as last value
            hum_last = hum
        
        """
        5. line Lux
        no scoring
        """
        # get value
        lux  = sensor.bh1750.data.get("lux")
        # next draw coord
        coord_y += font_height + offset_y + START_Y
        if lux_last != lux:
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            # draw value
            value = "{} lux".format(str(lux).replace(".", ","))
            tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color(VALUE_COLOR))
            # save as last value
            lux_last = lux

          
        # x-resets
        coord_x = START_X
        clear_width = tft.display.width - START_X - coord_x + offset_x
 
        """
        6. line CO2 min, max
        """
        # get values
        co2_max  = sensor.scd30.data.get("co2_max")
        co2_min  = sensor.scd30.data.get("co2_min")
        # next draw coord
        coord_y += font_height + offset_y + START_Y        
        if co2_max_last != co2_max or co2_min_last != co2_min:
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            # draw value
            value = "C02 min. {} - max. {}".format(co2_min, co2_max)
            tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color("GRAY"))
            # save as last value
            co2_max_last = co2_max
            co2_min_last = co2_min

        
        """
        7. line Temp min, max
        """        
        # get values
        temp_max  = sensor.scd30.data.get("temp_max")
        temp_min  = sensor.scd30.data.get("temp_min")
        # next draw coord
        coord_y += font_height + offset_y + START_Y
        if temp_max_last != temp_max or temp_min_last != temp_min:
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            # draw value
            value = "Temp. min. {} - max. {}".format(str(temp_min).replace(".", ","), str(temp_max).replace(".", ","))
            tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color("GRAY"))
            # save as last value
            temp_max_last = temp_max
            temp_min_last = temp_min

        # next draw coord
#         coord_y += font_height + offset_y + START_Y        
#         if sensor.mq2.data:
#             data = sensor.mq2.data
#             # draw text
#             for key, value in data.items():          
#                 text = "{} {}".format(key, str(value))
#                 tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("WHITE"))
#                 coord_y += font_height + offset_y
#             mq2_counter += 1
#             text = "Gas"
#             tft.display.draw_text(270, 180, text , tft.font, tft.color("RED"))
#             if mq2_counter >= 2:
#                 sensor.mq2.data = None
#                 mq2_counter = 0
#                 tft.display.draw_rectangle(270, 180, (font_width*len(text)), font_height, tft.color(CLEAR_COLOR))

        """
        8. line Warning, Info, etc.
        """
        # next draw coord
        coord_y += font_height + offset_y + START_Y
        
        if co2_warning is not None:
            if co2_warning_last != co2_warning:
                # clear area
                tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
                # draw value
                value = co2_warning
                tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color(co2_score_color))
                co2_warning_last = co2_warning
                await asyncio.sleep(1)
                lightstrip.cycle(color=co2_score_color)
        else:
            co2_warning_last = None
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
        
        if sensor.mq2.data is not None:
            # clear area
            tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            # draw value
            value = "Gas or Smoke detected"
            tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color("RED"))
            sensor.mq2.data = None
   
        """
        END slim progressbar
        """
        # compute time difference
        end_time = ticks_diff(ticks_ms(), start_time) / 1000
        if debug: print("time to displaying {} seconds".format(end_time))
        progressbar_timer = 0.3
        rect_height = 8
        rect_width = 103
        rect_x = 5
        rect_y = 225
        rect_range = 3
        if end_time < interval: progressbar_timer = (interval-end_time) / rect_range
        if debug: print("progressbar timeout {} seconds".format(progressbar_timer))
        outer_width = (rect_width*rect_range) + rect_x-3
        tft.display.draw_rectangle(rect_x-1, rect_y-1, outer_width, rect_height+2, tft.color("WHITE"))
        for i in range(rect_range):
            tft.display.fill_rectangle(rect_x, rect_y, rect_width, rect_height, tft.color("GREEN"))
            rect_x = rect_x + rect_width
            await asyncio.sleep(progressbar_timer)
        tft.display.fill_rectangle(4, rect_y-1, outer_width, rect_height+2, tft.color(CLEAR_COLOR))
        await asyncio.sleep(0.1)
        
        # big progress bar
#         rect_range = 3
#         rect_height = 20
#         rect_width = 310 // rect_range
#         rect_x = 5
#         rect_y = 215
#         outer_width = (rect_width*rect_range) + rect_x-3
#         tft.display.draw_rectangle(rect_x-1, rect_y-1, outer_width, rect_height+2, tft.color("WHITE"))
#         for i in range(rect_range):
#             tft.display.fill_rectangle(rect_x, rect_y, rect_width, rect_height, tft.color("GREEN"))
#             rect_x = rect_x + rect_width
#             await asyncio.sleep(0.5)
#         tft.display.fill_rectangle(4, 214, outer_width, rect_height+2, tft.color(CLEAR_COLOR))
#         await asyncio.sleep(0.1)

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


# main
def main():
    
    print("loading config...")
    
    # load app config
    config = Database("/app/app.db")
    
    # I2C
    I2C_SLOT = config.get("I2C").get("SLOT")
    SDA_PIN  = config.get("I2C").get("SDA")
    SCL_PIN  = config.get("I2C").get("SCL")
    
    # AS3935
    AS3935_INIT        = config.get("AS3935").get("INIT")
    AS3935_IRQ_PIN     = config.get("AS3935").get("IRQ_PIN")
    AS3935_INDOOR      = config.get("AS3935").get("INDOOR")
    AS3935_DISTURBER   = config.get("AS3935").get("DISTURBER")
    AS3935_CAPACITANCE = config.get("AS3935").get("CAPACITANCE")
    AS3935_INTERVAL    = config.get("AS3935").get("INTERVAL")
    
    # MQ2
    MQ2_INIT        = config.get("MQ2").get("INIT")
    MQ2_ANALOG_PIN  = config.get("MQ2").get("ANALOG_PIN")
    MQ2_DIGITAL_PIN = config.get("MQ2").get("DIGITAL_PIN")
    MQ2_INTERVAL    = config.get("MQ2").get("INTERVAL")
    MQ2_CALIBRATE   = config.get("MQ2").get("CALIBRATE")
    MQ2_BASEVOLTAGE = config.get("MQ2").get("BASEVOLTAGE")
    
    # LIGHTSTRIP
    LIGHTSTRIP_INIT     = config.get("LIGHTSTRIP").get("INIT")
    LIGHTSTRIP_DATA_PIN = config.get("LIGHTSTRIP").get("DATA_PIN") # Data Pin
    LIGHTSTRIP_PIXEL    = config.get("LIGHTSTRIP").get("PIXEL")    # Number of pixels
    
    # SPS30
    SPS30_INIT     = config.get("SPS30").get("INIT")     # use Sensor 
    SPS30_INTERVAL = config.get("SPS30").get("INTERVAL") # Loop async interval
    SPS30_UART     = config.get("SPS30").get("UART")     # UART Slot
    SPS30_RX       = config.get("SPS30").get("RX")       # RX Pin
    SPS30_TX       = config.get("SPS30").get("TX")       # TX Pin
    SPS30_SAMPLE   = config.get("SPS30").get("SAMPLE")   # default 1200
    SPS30_START    = config.get("SPS30").get("START")    # Start sensor
    
    # SCD30
    SCD30_INIT          = config.get("SCD30").get("INIT")          # use Sensor 
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
    
    # TFT
    TFT_INIT  = config.get("TFT").get("INIT")
    TFT_SPI   = config.get("TFT").get("SPI")
    TFT_MOSI  = config.get("TFT").get("MOSI")
    TFT_MISO  = config.get("TFT").get("MISO")
    TFT_SCK   = config.get("TFT").get("SCK")
    TFT_CS    = config.get("TFT").get("CS")
    TFT_DC    = config.get("TFT").get("DC")
    TFT_RESET = config.get("TFT").get("RESET")
    TFT_LED   = config.get("TFT").get("LED")
    if TFT_LED == False: TFT_LED = None
    
    # DISPLAY
    DISPLAY_INIT     = config.get("DISPLAY").get("INIT")
    DISPLAY_INTERVAL = config.get("DISPLAY").get("INTERVAL")
    
    # FONT
    FONT_FILE   = config.get("FONT").get("FILE")
    FONT_WIDTH  = config.get("FONT").get("WIDTH")
    FONT_HEIGHT = config.get("FONT").get("HEIGHT")
    
    del config
    
    # lightstrip
    lightstrip = Lightstrip(Pin(LIGHTSTRIP_DATA_PIN, Pin.OUT), pixel=LIGHTSTRIP_PIXEL)
    
    # async loops
    loop = asyncio.get_event_loop()
    
    # lightstrip demo
    loop.create_task(runLightstripDemo(lightstrip))
        
    # Initializing I2C sensors
    sensor = Sensors(i2c=None, debug=debug)
    
    # BH1750
    if BH1750_INIT: sensor.init_BH1750(i2c=None)
    
    # MQ2
    if MQ2_INIT:
        sensor.init_MQ2(
            pin_analog=MQ2_ANALOG_PIN,
            pin_trigger=Pin(MQ2_DIGITAL_PIN, Pin.IN),
            baseVoltage=MQ2_BASEVOLTAGE,
            calibrate=MQ2_CALIBRATE
        )
    
    # SCD30
    if SCD30_INIT: sensor.init_SCD30(i2c=None, start=SCD30_START, pause=SCD30_PAUSE)
        
    # SPS30
    if SPS30_INIT: sensor.init_SPS30(slot=SPS30_UART, rx=SPS30_RX, tx=SPS30_TX, sample=SPS30_SAMPLE)
      
    # AS3935
    if AS3935_INIT:
        loop.create_task(sensor.init_AS3935(
            i2c=None,
            pin_irq=Pin(AS3935_IRQ_PIN, Pin.IN),
            capacitance=AS3935_CAPACITANCE,
            indoor=AS3935_INDOOR,
            disturber=AS3935_DISTURBER
        ))
    
    if DISPLAY_INIT:        
        print("\ndisplay initializing...")
        
        # DISPLAY
        tft = Display(cs=TFT_CS, dc=TFT_DC, reset=TFT_RESET, width=320, height=240, rotation=90) # horizontal
        #tft = Display(cs=TFT_CS, dc=TFT_DC, reset=TFT_RESET, width=240, height=320, rotation=0) # vertical
        
        # FONT
        tft.setFont(FONT_FILE, FONT_WIDTH, FONT_HEIGHT)
        font_height = tft.font_height
        font_width = tft.font_width
        
        START_X = tft.display.width // 4
        START_Y = tft.display.height // 6
        coord_y = START_Y
        offset_y = 4
        line = 1
        
        if debug:
            text = "DEBUG MODUS"
            color= "YELLOW"
        else:
            text = "Environment Monitoring"
            color= "LIME"
        tft.display.draw_text(5, 10, text, tft.font, tft.color(color))

        # border
        tft.display.draw_rectangle(START_X-offset_y, START_Y-offset_y, tft.display.width-120, tft.display.height-60, tft.color("WHITE"))    

        text = "display initialized"
        print(text)
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("YELLOW GREEN"))
        
        text = "lightstrip initialized"
        print(text)
        coord_y = START_Y + (font_height*line) + offset_y
        line += 1
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("YELLOW GREEN"))
        
        text = "sensors initialized"
        print(text)
        coord_y = START_Y + (font_height*line) + offset_y
        line += 1
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("YELLOW GREEN"))
        
        text = "web socket"
        print(text)
        coord_y = START_Y + (font_height*line) + offset_y
        line += 1    
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("GRAY"))
        
        text = "loops..."
        print(text)
        coord_y = START_Y + (font_height*line) + offset_y
        line += 1    
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("CYAN"))  
        
        text = "displaying..."
        print(text)
        coord_y = START_Y + (font_height*line) + offset_y
        line += 1    
        tft.display.draw_text(START_X, coord_y, text, tft.font, tft.color("CYAN"))

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
        
        # show system status
        if debug:
            loop.create_task(showSystemState(tft))
        else:
            state.set('ready', True)
    
    else:
        state.set('ready', True)
    
    # Watchdog loops
    if hasattr(sensor, 'scd30'):  loop.create_task(runWatchdogCO2(sensor.scd30, interval=SCD30_INTERVAL))
    if hasattr(sensor, 'bh1750'): loop.create_task(runWatchdogLux(sensor.bh1750, interval=BH1750_INTERVAL))
    if hasattr(sensor, 'sps30'):  loop.create_task(runWatchdogDust(sensor.sps30, interval=SPS30_INTERVAL))
    if hasattr(sensor, 'as3935'): loop.create_task(runWatchdogLightning(sensor.as3935, lightstrip, interval=AS3935_INTERVAL))
    if hasattr(sensor, 'mq2'):    loop.create_task(runWatchdogGas(sensor.mq2, lightstrip, interval=MQ2_INTERVAL))
    
    # Counter loop
    loop.create_task(runCounter(interval=1))
    
    # WIFI reconnecting loop
    reconnect = state.get('reconnect')
    if reconnect > 0:
        loop.create_task(runReconnect(interval=reconnect))
    
    # Wait for state ready
    loop.run_until_complete(waitfor_ready())
    
    # Main loop
    loop.create_task(showSensorData(tft, sensor, lightstrip, interval=DISPLAY_INTERVAL))
    
    # Tasks loop forever
    loop.run_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')

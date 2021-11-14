from machine import Pin
from time import sleep, sleep_ms, localtime, mktime, ticks_ms, ticks_diff
import uasyncio as asyncio

# Core libs
from core.database import Database

# App libs
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
    utc = system.get("UTC"),
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

# Lightstrip Demo
async def runLightstripDemo(lightstrip):
    while not app.get('ready'):
        lightstrip.each( 1, color="DARK ORANGE", clear=False)
        await asyncio.sleep(0.5)
        lightstrip.clear()
        lightstrip.each( 2, color="DARK ORANGE", clear=False)
        await asyncio.sleep(0.5)
        lightstrip.clear()
    await lightstrip.bounce(color="GREEN")

# WiFi loop
async def runReconnect(interval=3600, interval_if=600, retrys=3):
    retry = 0
    from core.wifi import smart_connect, is_connected, get_ip, get_ap_ip, start_ap, stop_ap
    while interval > 0:
        await asyncio.sleep(interval)
        if debug: print('network' , end=' ')
        if state.get('wifi') and not is_connected():
            print('reconnecting...')
            smart_connect()
            #connect()
            if is_connected():
                if state.get('ap_if') and retry == retrys:
                    stop_ap()
                    state.set("ap_ip_address", "0.0.0.0")
                retry = 0
                state.set("connected", True)
                state.set("ip_address", get_ip())
                interval = state.get('reconnect')
                if state.get('timesync') is not True:
                    from ntptime import settime
                    from core.timezone import Timezone
                    settime()
                    Timezone(state.get('utc')).offset()          
                    state.set('timesync', True)
                    if debug: print('time synchronized')
            else:
                state.set("connected", False)
                state.set("ip_address", "0.0.0.0")
                if retry == 0: interval = interval_if
                if retry != retrys: retry += 1
            # Start Access Point as fallback when reaching retrys
            if retry == retrys and state.get('ap_if'):
                start_ap()
                state.set("ap_ip_address", get_ap_ip())
                interval = 0

# Logger loop
async def runLogger(sensor, config):
    
    # config
    LOG_INTERVAL = config.get("INTERVAL")
    LOG_PATH     = config.get("PATH")
    LOG_FILE     = config.get("FILE")
    LOG_MIMETYPE = config.get("MIMETYPE")
    LOG_TOSDCARD = config.get("TOSDCARD")
    LOG_TIME     = config.get("TIME")
    
    await asyncio.sleep(20)
    data, i = [], 1
    
    while 1:
        tmp = {}
        # log data to file
        if time()[0:5] == LOG_TIME:
            if debug: print("write file...")
            data, i = [], 1
            await asyncio.sleep(60-LOG_INTERVAL)
        if debug: print("logging...")
        if hasattr(sensor, 'scd30'):
            if debug: print("log scd30 data")
            tmp = sensor.scd30.data
            tmp.update({"id": i, "sensor": "scd30", "timestamp": timestamp()})
            data.append(tmp)
        if hasattr(sensor, 'mq2'):
            if debug: print("log mq2 data")
            tmp = sensor.mq2.data
            if len(tmp) != 0:
                tmp.update({"id": i, "sensor": "mq2", "timestamp": timestamp()})
                data.append(tmp)
        if hasattr(sensor, 'bh1750'):
            if debug: print("log bh1750 data")
            tmp = sensor.bh1750.data
            tmp.update({"id": i, "sensor": "bh1750", "timestamp": timestamp()})
            data.append(tmp)
        if hasattr(sensor, 'sps30'):
            print("log sps30 data")
        print(i)
        i += 1
        await asyncio.sleep(LOG_INTERVAL)

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
            print(co2)
            print(temp)
            print(temp)
            if len(scd30.data) != 0 and co2 is not None and temp is not None:
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
                'error': 0,
                'time': time(),
                "date": date()
                }
            if debug:
                print("[SCD30] CO2: {} ppm | Temp.: {:2.1f} °C | Hum.: {} % | akt.".format(co2, temp, relh))
                print("[SCD30] CO2: {} ppm | Temp.: {:2.1f} °C | Hum.: {} % | max.".format(co2_max, temp_max, relh_max))
                print("[SCD30] CO2: {} ppm | Temp.: {:2.1f} °C | Hum.: {} % | min.".format(co2_min, temp_min, relh_min))            
        except Exception as e:
            scd30.data = {'error': 1}
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
                print("SPS30 read error! counts {}, {}".format(err_read, e))
            pass
    await asyncio.sleep(interval)

# Display system states
async def displaySystemState(tft):
    
    app.set('ready', False)
    boot = Database("/boot.db")
    
    font_height = tft.font_height
    font_width = tft.font_width

    # adjustable coords for text to line distance
    offset_y, offset_x = 2, 6
    border = True
    
    # clearing
    tft.display.clear()
    
    # page border
    if border:
        tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color("WHITE"))
        border_px = 1
    
    # const 1px border
    BORDER_Y = BORDER_X = border_px
    
    # start coords draw text
    START_X = BORDER_X + offset_x
    START_Y = BORDER_Y + offset_y
    
    # Page 1
    line, max_lines = 1, 7
    coord_y = START_Y
    coord_x, coord_x1 = START_X, 180
    
    # header
    text = "System State"
    tft.display.draw_text(START_X, START_Y, text, tft.font, tft.color("CYAN"))
    # draw line
    coord_y = START_Y + font_height + offset_y
    tft.display.draw_hline(0, coord_y, tft.display.width, tft.color("WHITE"))
    
    async def progressbar():
        # progress bar
        rect_height = 6
        rect_width = 31
        rect_x = 3
        rect_y = 230
        rect_range = 10
        outer_width = (rect_width*rect_range) + rect_x-3
        tft.display.draw_rectangle(rect_x-1, rect_y-1, outer_width, rect_height+2, tft.color("WHITE"))
        for i in range(rect_range):
            tft.display.fill_rectangle(rect_x, rect_y, rect_width, rect_height, tft.color("GREEN"))
            rect_x = rect_x + rect_width
            await asyncio.sleep(0.5)
    
    # coord-y vertical line
    vline_y = coord_y
    # system info#
    for key in system.keys():
        if line == max_lines:
            tft.display.draw_vline(coord_x1-offset_x, vline_y, coord_y-START_Y-font_height, tft.color("WHITE"))
            await progressbar()
            line = 1
            coord_y = START_Y + font_height + offset_y
            tft.display.fill_rectangle(1, coord_y+1, tft.display.width-(BORDER_X*2), tft.display.height-coord_y-(BORDER_Y*2), tft.color("BLACK"))    
        value = app.get(key)
        if not value:
            value = system.get(key)
            if isinstance(value, bool): value = "YES" if value else "NO"
            coord_y += START_Y
            tft.display.draw_text(coord_x, coord_y, key, tft.font, tft.color("WHITE"))
            tft.display.draw_text(coord_x1, coord_y, str(value), tft.font, tft.color("WHITE"))
            # draw horizontal line
            coord_y += font_height + offset_y
            tft.display.draw_hline(0, coord_y, tft.display.width, tft.color("WHITE"))
            line += 1
    # draw vertical line
    tft.display.draw_vline(coord_x1-offset_x, vline_y, coord_y-START_Y-font_height, tft.color("WHITE"))
    
    await progressbar()
    
    # del database object
    del boot
    
    # ready for main loop
    app.set('ready', True)

# Display loop
async def displaySensorData(tft, sensor, lightstrip, interval=2):
    
    await asyncio.sleep(interval)
    
    # nightmode 2 = off
    nightmode = 2
    
    # init nightmode
    # -1 mode on, state undefined
    if app.get("nightmode"): nightmode = -1
    # TODO: is now between nightstart, nightend
    # 1 = on, 0 = off
    # nightmode = 1
        
    # font width, heigt for calculating coords
    font_height, font_width = tft.font_height, tft.font_width
    
    # page border setting
    border = True
    border_px = 0
    
    # progressbar setting
    out_time = 0.3
    rect_width, rect_range = 310, 3
    progressbar_time = interval / rect_range
    rect_progress = rect_width // rect_range
    rect_x, rect_y, rect_height = 5, 228, 8
    rect_bar_x = rect_x
    outer_width = rect_width + rect_x - 3
        
    # color setting
    BORDER_COLOR = ITEM_COLOR = LINE_COLOR = "WHITE"
    VALUE_COLOR, CLOCK_COLOR, HEADER_COLOR, CLEAR_COLOR  = "CYAN", "YELLOW", "BLUE", "BLACK"

    # adjustable coords for text to line distance
    offset_y, offset_x = 2, 6
    
    # clearing
    tft.display.clear()
    
    # page border
    if border:
        tft.display.draw_rectangle(0, 0, tft.display.width, tft.display.height, tft.color(BORDER_COLOR))
        border_px = 1
    
    # const 1px border
    BORDER_Y = BORDER_X = border_px
    
    # start coords draw text
    START_X = BORDER_X + offset_x
    START_Y = BORDER_Y + offset_y
    
    """
    NOTE: x-coords need to be static values
    it's not possible to calculate usefull coordinates with length of string * font-width
    to get coord for the next text in line
    the declacred font-width seems to be the max-width of a letter
    letters need a different size of pixels - M an I for example
    Declace static display areas |x|x1|x2|
    """
    coord_x = START_X
    coord_x1, coord_x2 = 90, 210
    netstate_coord_x = 275

    """
    set display clearing spaces line, x, x1, x2
    """
    clear_width      = tft.display.width - START_X - BORDER_X
    clear_width_x    = coord_x1 - START_X - offset_x
    clear_width_x1   = tft.display.width - clear_width_x - (tft.display.width - coord_x2) - (offset_x*2) - START_X
    clear_width_x2   = tft.display.width - clear_width_x - clear_width_x1 - (offset_x*2) - START_X - BORDER_X


    # clocktime, date
    now = time()[0:5]
    today = date()
    
    """
    First line header
    """
    # draw clock time
    tft.display.draw_text(START_X, START_Y, now, tft.font, tft.color(CLOCK_COLOR))
    # draw heading
    text = "ENVIRONMENT"
    tft.display.draw_text(coord_x1, START_Y, text, tft.font, tft.color(HEADER_COLOR)) 
    # draw line
    coord_y = START_Y + font_height
    tft.display.draw_hline(0, coord_y, tft.display.width, tft.color(LINE_COLOR))
    
    # is warning cleared
    warning_cleared = False
    
    # last connection state
    last_connected = None
    
    # set mectric for sensor
    # order by line drawing
    metrics = []
    max_metrics = 4
    
    if sensors.get('scd30'):
        # define metrics
        metrics.append('CO2')
        metrics.append('Temp.')
        metrics.append('Hum.')
        # init sensor values
        CO2_WARNING_VALUE = 800
        co2_warning, co2_warning_last, co2_color_last = None, None, None
        co2_last, co2_max_last, co2_min_last = None, None, None
        temp_last, temp_max_last, temp_min_last, hum_last = None, None, None, None
    if sensors.get('sps30'):
        sps30 = True
        # define metrics
        # init sensor values
    if sensors.get('bh1750'):
        # define metric
        metrics.append('Light.')
        # init sensor value
        lux_last = None
    if sensors.get('mq2'):
        mq2_warning = None
    
    if len(metrics) > max_metrics:
        raise Exception("invalid sensor config: too many metrics set ({}/{})".format(len(metrics), max_metrics))
    
    # coord-y vertical lines
    vline_y = coord_y
    
    # draw metrics, horizontal lines
    for metric in metrics:
        coord_y += START_Y
        tft.display.draw_text(START_X, coord_y, metric, tft.font, tft.color(ITEM_COLOR))
        # draw horizontal line
        coord_y += font_height + offset_y
        tft.display.draw_hline(0, coord_y, tft.display.width, tft.color(LINE_COLOR))
    
    # draw vertical lines
    tft.display.draw_vline(coord_x1-offset_x, vline_y, coord_y-START_Y-font_height, tft.color(LINE_COLOR))
    tft.display.draw_vline(coord_x2-offset_x, vline_y, coord_y-START_Y-font_height, tft.color(LINE_COLOR))
    
    # score sensor value
    scoring = Scoring(debug=debug)
    
    # reset values max, min
    reset_time = "00:00"
    reset_done = False
    reset = False
    
    while 1:
        # counter to calculate restinterval
        refresh_start = ticks_ms()
        
        # clocktime init value
        clocktime = time()[0:5]
        
        if app.get("nightmode") or nightmode < 0:
            if clocktime == app.get("nightstart"): nightmode = 1
            if clocktime == app.get("nightend"):   nightmode = 0
        
        if clocktime == reset_time and not reset_done: reset = True
                    
        """
        Line header
        Refresh clocktime
        Refresh network state
        """
        line = 0
        if now != clocktime:
            reset_done = False
            now = clocktime
            if state.get("timesync"):
                tft.display.fill_rectangle(START_X, START_Y, clear_width_x, font_height, tft.color(CLEAR_COLOR))
                tft.display.draw_text(START_X, START_Y, now, tft.font, tft.color(CLOCK_COLOR))
        connected = state.get('connected')
        if connected != last_connected:
            offset_coord_x = 0
            last_connected = connected
            text, color = "OFF", "GRAY"
            if state.get('wifi'): text, color = "WiFi", "GREEN"
            if not connected: color = "DARK ORANGE"
            if state.get('ap'): text, color = "AP", "DEEP SKY BLUE"
            if state.get('ap_if') and state.get('wifi') and not connected: text, offset_coord_x = "WiFi+AP", 40
            tft.display.fill_rectangle(netstate_coord_x-offset_coord_x, START_Y, tft.display.width-netstate_coord_x-offset_x, font_height, tft.color(CLEAR_COLOR))
            tft.display.draw_text(netstate_coord_x-offset_coord_x, START_Y, text, tft.font, tft.color(color))
        
        """
        NOTE:
        reset coord-y to draw first value (after headline)
        """
        line = 1
        coord_y = START_Y + font_height + offset_y
        
        """scd30
        Area:    CO2, Scorecolor
        Coords:  x1, x2 
        Scoring: value
        """
        if sensors.get('scd30'):
            co2  = sensor.scd30.data.get("co2")
            color = co2_color_last
            if co2_last != co2:
                # scoring value
                score = scoring.co2(co2)
                color = scoring.color(score)                
                value = "{} ppm".format(co2)
                if co2 >= CO2_WARNING_VALUE:
                    co2_warning = "CO2 score is {}".format(score)
                    co2_score_color = color
                else:
                    co2_score_color = VALUE_COLOR
                    co2_warning = None
                if sensor.scd30.data.get("error") == 1:
                    co2_warning = "SCD30 read error!"
                    co2_score_color = "RED"
                # clear area x1
                tft.display.fill_rectangle(coord_x1, coord_y, clear_width_x1, font_height, tft.color(CLEAR_COLOR))
                # draw x1 value
                tft.display.draw_text(coord_x1, coord_y, value, tft.font, tft.color(co2_score_color))
                # save as last value
                co2_last = co2
            if co2_color_last != color:
                # draw x2 score color
                tft.display.fill_rectangle(coord_x2-offset_x+BORDER_X, coord_y-offset_y+BORDER_Y, clear_width_x2+START_X-BORDER_X*2, font_height+START_Y+BORDER_Y, tft.color(color))
                # save as last value
                co2_color_last = color

        """scd30
        Area:    temperature, difference or heatindex
        Coords:  x1, x2
        Scoring: heatindex
        """
        # next draw coord-y
        line += 1
        coord_y += font_height + offset_y + START_Y
        if sensors.get('scd30'):
            # get sensor values
            temp  = sensor.scd30.data.get("temp")
            hum = sensor.scd30.data.get("relh")        
            if temp_last != temp:
                color = ITEM_COLOR
                value = "{} C".format(str(temp).replace(".", ","))
                # clear x1 area
                tft.display.fill_rectangle(coord_x1, coord_y, clear_width_x1, font_height, tft.color(CLEAR_COLOR))
                # draw x1 value
                tft.display.draw_text(coord_x1, coord_y, value, tft.font, tft.color(VALUE_COLOR))
                # scoring heatindex or temperature
                hi, score = scoring.heatindex(temp, hum)
                if hi is None:
                    # calc difference          
                    temp_diff = temp - temp_last if temp_last is not None else 0
                    temp_diff = round(temp_diff, 1)
                    if temp_diff >= 0: value = "+{}".format(str(temp_diff).replace(".", ","))
                    else: value = "{}".format(str(temp_diff).replace(".", ","))
                else:
                    color = scoring.color(score)
                    value = "HI {} C".format(str(hi).replace(".", ","))
                    hi_warning = "Heatindex is {}".format(score)
                    hi_score_color = color
                # draw difference or hi
                tft.display.fill_rectangle(coord_x2, coord_y, clear_width_x2, font_height, tft.color(CLEAR_COLOR))            
                tft.display.draw_text(coord_x2, coord_y, value, tft.font, tft.color(ITEM_COLOR))
                # save as last value
                temp_last = temp
        
        """scd30
        Area:   humidity, difference
        Coords: x1, x2
        """
        # next draw coord
        line += 1
        coord_y += font_height + offset_y + START_Y
        if sensors.get('scd30'):
            if hum_last != hum:
                score = scoring.humidity(hum)
                color = scoring.color(score)
                value = "{} %".format(str(hum))
                # clear area
                tft.display.fill_rectangle(coord_x1, coord_y, clear_width_x1, font_height, tft.color(CLEAR_COLOR))
                # draw value
                tft.display.draw_text(coord_x1, coord_y, value, tft.font, tft.color(VALUE_COLOR))
                # draw difference          
                hum_diff = hum - hum_last if hum_last is not None else 0
                if hum_diff >= 0: value = "+{}".format(hum_diff)
                else: value = "{}".format(hum_diff)
                tft.display.fill_rectangle(coord_x2, coord_y, clear_width_x2, font_height, tft.color(CLEAR_COLOR))            
                tft.display.draw_text(coord_x2, coord_y, value, tft.font, tft.color(ITEM_COLOR))  
                # save as last value
                hum_last = hum
        
        """bh1750
        Area:   lux, difference
        Coords: x1, x2
        """
        # next draw coord
        line += 1
        coord_y += font_height + offset_y + START_Y
        if sensors.get('bh1750'):
            # get sensor values
            lux = sensor.bh1750.data.get("lux")        
            if lux_last != lux:
                # clear area
                tft.display.fill_rectangle(coord_x1, coord_y, clear_width_x1, font_height, tft.color(CLEAR_COLOR))
                # draw value
                value = "{} lux".format(str(lux).replace(".", ","))
                tft.display.draw_text(coord_x1, coord_y, value, tft.font, tft.color(VALUE_COLOR))
                # draw difference          
                lux_diff = lux - lux_last if lux_last is not None else 0
                lux_diff = round(lux_diff,1)
                if lux_diff >= 0: value = "+{}".format(str(lux_diff).replace(".", ","))
                else: value = "{}".format(str(lux_diff).replace(".", ","))
                tft.display.fill_rectangle(coord_x2, coord_y, clear_width_x2, font_height, tft.color(CLEAR_COLOR))            
                tft.display.draw_text(coord_x2, coord_y, value, tft.font, tft.color(ITEM_COLOR)) 
                # save as last value
                lux_last = lux
        
        """scd30
        Line:  CO2 min, max
        Coord: x
        """
        # next draw coord
        line += 1
        coord_y += font_height + offset_y + START_Y
        if sensors.get('scd30'):     
            # reset max
            if reset: sensor.scd30.data["co2_max"] = sensor.scd30.data.get("co2_min")
            # get values
            co2_min = sensor.scd30.data.get("co2_min")
            co2_max = sensor.scd30.data.get("co2_max")
            if co2_max_last != co2_max or co2_min_last != co2_min:
                # clear area
                tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
                # draw value
                value = "CO2 min. {} - max. {}".format(co2_min, co2_max)
                tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color("AQUA MARINE"))
                # draw horizontal line
                line_y = coord_y + font_height + offset_y
                tft.display.draw_hline(0, line_y, tft.display.width, tft.color(LINE_COLOR))
                # save as last value
                co2_max_last = co2_max
                co2_min_last = co2_min

        
        """scd30
        Line:  Temp min, max
        Coord: x
        """
        # next draw coord
        line += 1
        coord_y += font_height + offset_y + START_Y  
        if sensors.get('scd30'):
            # reset min, max
            if reset: sensor.scd30.data["temp_max"] = 0
            if reset: sensor.scd30.data["temp_min"] = 0     
            # get values
            temp_max  = sensor.scd30.data.get("temp_max")
            temp_min  = sensor.scd30.data.get("temp_min")
            if temp_max_last != temp_max or temp_min_last != temp_min:
                # clear area
                tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
                # draw value
                value = "Temp. min. {} - max. {}".format(str(temp_min).replace(".", ","), str(temp_max).replace(".", ","))
                tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color("AQUA MARINE"))
                # draw horizontal line
                line_y = coord_y + font_height + offset_y
                tft.display.draw_hline(0, line_y, tft.display.width, tft.color(LINE_COLOR))            
                # save as last value
                temp_max_last = temp_max
                temp_min_last = temp_min
        
        """
        Line:  Warnings (last line)
        Coord: x
        """
        # next draw coord
        line += 1
        coord_y += font_height + offset_y + START_Y
        
        # gas or smoke warning
        if sensors.get('mq2'):
            if len(sensor.mq2.data) != 0:
                # clear area
                tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
                warning_cleared = True
                # draw value
                value = "Gas or Smoke detected"
                tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color("RED"))
                sensor.mq2.data = {}
                if nightmode != 1: await lightstrip.fade()
                else: lightstrip.cycle(color="RED", times=2)
        
        # co2 warning
        if sensors.get('scd30'):
            if co2_warning is not None:
                if co2_warning_last != co2_warning or warning_cleared:
                    # clear area
                    tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
                    # draw value
                    value = co2_warning
                    tft.display.draw_text(coord_x, coord_y, value, tft.font, tft.color(co2_score_color))
                    co2_warning_last = co2_warning
                    warning_cleared = False
                    await lightstrip.cycle(color=co2_score_color)
                    if nightmode != 1: lightstrip.color(color=co2_score_color)
            else:
                co2_warning_last = None
                lightstrip.clear()
                # clear area
                tft.display.fill_rectangle(coord_x, coord_y, clear_width, font_height, tft.color(CLEAR_COLOR))
            
        # reset init
        if reset: reset_done = True
        reset = False
        
        """
        END: progressbar
        """
        progressbar_time = interval / rect_range
        rect_bar_x = rect_x        
        # draw progressbar
        tft.display.draw_rectangle(rect_x-BORDER_X, rect_y-BORDER_Y, outer_width, rect_height+2, tft.color("WHITE"))
        # compute time difference
        refresh_time = ticks_diff(ticks_ms(), refresh_start) / 1000
        if debug: print("time to refresh display {} seconds".format(refresh_time))
        if refresh_time < interval: progressbar_time = (interval-refresh_time) / rect_range
        if debug: print("progressbar timeout {} seconds".format(progressbar_time))        
        for i in range(rect_range):
            tft.display.fill_rectangle(rect_bar_x, rect_y, rect_progress, rect_height, tft.color("GREEN"))
            rect_bar_x += rect_progress
            await asyncio.sleep(progressbar_time)
        tft.display.fill_rectangle(rect_x-BORDER_X, rect_y-BORDER_Y, outer_width, rect_height+2, tft.color(CLEAR_COLOR))
        await asyncio.sleep(out_time)

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

def datetime():
    t = localtime()
    return "{}{:02d}{:02d}{:02d}{:02d}{:02d}".format(t[0], t[1], t[2], t[3], t[4], t[5])

def timestamp():
    return mktime(localtime())


# main
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
    lightstrip = Lightstrip(Pin(LIGHTSTRIP_DATA_PIN, Pin.OUT), pixel=LIGHTSTRIP_PIXEL)
    
    print("\nloops...")
    
    # Async loops
    loop = asyncio.get_event_loop()
    
    # Initializing I2C sensors
    sensor = Sensors(i2c=None, debug=debug)
    
    # MQ2
    if MQ2_INIT:
        sensor.init_MQ2(
            pin_analog=MQ2_ANALOG_PIN,
            pin_trigger=Pin(MQ2_DIGITAL_PIN, Pin.IN),
            baseVoltage=MQ2_BASEVOLTAGE,
            calibrate=MQ2_CALIBRATE
        )
    
    # Lightstrip demo
    loop.create_task(runLightstripDemo(lightstrip))
    
    # BH1750
    if BH1750_INIT: sensor.init_BH1750(i2c=None)
    
    # SCD30
    if SCD30_INIT: sensor.init_SCD30(i2c=None, start=SCD30_START, pause=SCD30_PAUSE)
    
    # SPS30
    if SPS30_INIT: sensor.init_SPS30(port=SPS30_PORT, rx=SPS30_RX, tx=SPS30_TX, start=SPS30_START, clean=SPS30_CLEAN, sample=SPS30_SAMPLE)
    
    # AS3935
    if AS3935_INIT:
        loop.create_task(sensor.init_AS3935(
            i2c=None,
            pin_irq=Pin(AS3935_IRQ_PIN, Pin.IN),
            capacitance=AS3935_CAPACITANCE,
            indoor=AS3935_INDOOR,
            disturber=AS3935_DISTURBER
        ))
        
    display = False
    # ILI9341
    if DISPLAY_INIT:
        print("\ndisplay initializing...")
        rotation = 90  # horizontal:90, vertical:0
        # DISPLAY
        tft = Display(cs=TFT_CS, dc=TFT_DC, reset=TFT_RESET, width=320, height=240, rotation=rotation, debug=debug)
        # FONT
        if tft is not None: tft.setFont(FONT_FILE, FONT_WIDTH, FONT_HEIGHT)
        if tft.font is not None: display = True
    
    # show system status
    if display and not debug: loop.create_task(displaySystemState(tft))
    else: app.set('ready', True)
    
    # Watchdog loops
    if hasattr(sensor, 'scd30'):
        sensors.set('scd30', True)
        loop.create_task(runWatchdogCO2(sensor.scd30, interval=SCD30_INTERVAL))
    if hasattr(sensor, 'bh1750'):
        sensors.set('bh1750', True)
        loop.create_task(runWatchdogLux(sensor.bh1750, interval=BH1750_INTERVAL))
    if hasattr(sensor, 'sps30'):
        sensors.set('sps30', True)
        loop.create_task(runWatchdogDust(sensor.sps30, interval=SPS30_INTERVAL))
    if hasattr(sensor, 'as3935'):
        sensors.set('as3935', True)
        loop.create_task(runWatchdogLightning(sensor.as3935, lightstrip, interval=AS3935_INTERVAL))
    if hasattr(sensor, 'mq2'):
        sensors.set('mq2', True)
        loop.create_task(runWatchdogGas(sensor.mq2, interval=MQ2_INTERVAL))
    
    # WiFi loop
    if state.get('reconnect') > 0: loop.create_task(runReconnect(state.get('reconnect'), 600, 3))
    
    # Logger loop
    if LOGGER_INIT: loop.create_task(runLogger(sensor, LOGGER_CONFIG))
    
    # Wait for state ready
    loop.run_until_complete(waitfor_ready())
    
    # Display loop
    if display: loop.create_task(displaySensorData(tft, sensor, lightstrip, interval=DISPLAY_INTERVAL))
    
    # Tasks loop forever
    loop.run_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')

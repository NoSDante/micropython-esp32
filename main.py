import gc
from core.database import Database

# main
print("main...")

"""
Define db-files
"""
BOOT_DATABASE = "/boot.db"
SYSTEM_DATABASE = "/system.db"


def init():
    """
    Get init params from boot db-file
    Set default params as fallback
    """
    try:
        boot = Database(BOOT_DATABASE)
    except:
        print("boot config missing")
        boot = {
            "DEBUG": False,
            "NETWORK":
                {
                    "WIFI": False,
                    "AP_IF": False,
                    "AP": True
                }
        }

    """
    Default system states
    bool: mounted:   is SD-Card mounted
    bool: timesync:  is time sync
    bool: ap:        start Access Point
    bool: ap_if:     start Access Point, if wifi not connected
    bool: wifi:      use WiFi
    bool: rtc:       use rtc
    int:  utc:       set a timezone
    int:  reconnect: time for WiFi try-reconnecting loop 0=off
    """
    debug, sdcard, rtc, timesync = False, False, False, False
    wifi, smart, connected, ap, ap_if, = False, False, False, False, False
    ip_address, ap_ip_address, rtc_modul, essid = "0.0.0.0", "0.0.0.0", "", ""
    reconnect, utc = 0, 0

    """
    DEBUG
    """
    debug = boot.get("DEBUG")
    test = False
    if debug:
        """
        reset, wake return codes
        0 Undefined
        1 Power reboot
        2 External reset or wake-up from Deep-sleep
        4 Hardware WDT reset
        """
        from machine import reset_cause, wake_reason
        print("\n----- MACHINE -----")
        print("reset cause:", reset_cause())
        print("wake reason:", wake_reason())
        device = boot.get("DEVICE")
        if device is not None and test:
            print("\n----- DEVICE -----")
            for key, value in device.items(): print("{}: {}".format(key, value))

    """
    SDCard
    """
    if boot.get("SDCARD"):
        from core.sdcard import mounting
        sdcard = mounting(
            slot=boot.get("SDCARD").get("SPI"),
            path=boot.get("SDCARD").get("PATH"),
            width=boot.get("SDCARD").get("WIDTH"),
            cs=boot.get("SDCARD").get("CS"),
            miso=boot.get("SDCARD").get("MISO"),
            mosi=boot.get("SDCARD").get("MOSI"),
            sck=boot.get("SDCARD").get("SCK"),
            debug=debug
        )

    gc.collect()

    """
    NETWORK
    """
    if boot.get("NETWORK"):
        print("\nnetwork...")
        from core.wifi import smart_connect, connect, disconnect, is_connected, get_ip, get_essid, get_ap_ip, start_ap
        network = boot.get("NETWORK")
        ap_if = network.get("AP_IF")
        ap_start = False
        if network.get("WIFI") or network.get("FOR_TIMESYNC"):
            # stop_ap()
            wifi = network.get("WIFI")
            reconnect = network.get("RECONNECT")
            timezone = boot.get("TIMEZONE")
            if timezone: utc = timezone.get("UTC")
            smart = network.get("SMART")
            if smart:
                smart_connect()
            else:
                connect()
            if is_connected():
                connected = True
                ip = get_ip()
                if ip is not None: ip_address = ip
                essid = get_essid()
                if essid is None: essid = ""
                """
                Timezone UTC+ to set an offset for the RTC
                """
                from core.timezone import Timezone
                if debug: print("timezone:", timezone.get("ZONE"))
                """
                timeset ntptime
                """
                try:
                    from ntptime import settime
                    settime()
                    Timezone(utc).offset()
                    timesync = True
                    print('time synchronized')
                except Exception as e:
                    print('setting time failed', e)
                """
                timeset fallback
                """
                if not timesync:
                    print('timeset fallback...')
                    try:
                        Timezone(utc).settime()
                        timesync = True
                        print('time synchronized')
                    except Exception as e:
                        print('setting time failed', e)
                if wifi == False and network.get("FOR_TIMESYNC"):
                    disconnect()
                    connected, ip_address, essid = False, "0.0.0.0", ""
            elif ap_if:
                ap_start = True
        elif network.get("AP"):
            ap = ap_start = True
        if ap_start:
            start_ap()
            ip = get_ap_ip()
            if ip is not None: ap_ip_address = ip

    """
    RTC
    """
    if boot.get("RTC"):
        print("\nRTC...")
        from machine import I2C, Pin, RTC
        i2c = I2C(
            boot.get("I2C").get("SLOT"),
            scl=Pin(boot.get("I2C").get("SCL")),
            sda=Pin(boot.get("I2C").get("SDA"))
        )
        rtc_modul = boot.get("RTC").get("MODUL")
        # DS1307
        if rtc_modul.lower() == "ds1307":
            ds1307 = None
            try:
                from lib.ds1307 import DS1307
                ds1307 = DS1307(i2c)
            except ImportError as e:
                print("cannot import module", e)
            # synchronize RTC
            if ds1307 is not None:
                if timesync:
                    ds1307.datetime(RTC().datetime())
                    if debug: print("synchronized RTC", ds1307.datetime())
                else:
                    # initialize RTC
                    if debug: print("RTC Modul:", rtc_modul)
                    rtc = True
                    if ds1307.datetime() == "2000, 1, 1, 0, 0, 0, 0, 0":
                        rtc_modul = "SETTIME"
                    else:
                        # probably correct
                        if debug: print(rtc_modul, ds1307.datetime())
                        dt = ds1307.datetime()
                        # ( year,month,day,weekday,hour,minute,second,microsecond )
                        RTC().init((dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], 0))
                        timesync = True
                        if debug: print("RTC", RTC().datetime())
        # DS3231
        if rtc_modul.lower() == "ds3231":
            ds3231 = None
            try:
                from lib.ds3231 import DS3231
                ds3231 = DS3231(i2c)
            except ImportError as e:
                print("cannot import module", e)
                if ds1307 is not None:
                    # synchronize RTC
                    if timesync:
                        ds3231.DateTime(RTC().datetime())
                        if debug: print("synchronized RTC", ds3231.DateTime())
                    else:
                        # initialize RTC
                        if debug: print("RTC Modul:", rtc_modul)
                        rtc = True
                        if ds3231.DateTime() == "2000, 1, 1, 0, 0, 0, 0, 0":
                            rtc_modul = "SETTIME"
                        else:
                            # probably correct
                            if debug: print(rtc_modul, ds3231.DateTime())
                            dt = ds3231.DateTime()
                            # ( year,month,day,weekday,hour,minute,second,microsecond )
                            RTC().init((dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], 0))
                            timesync = True
                            if debug: print("RTC", RTC().datetime())

    """
    Save states
    """
    system = Database(SYSTEM_DATABASE, create=True)
    system.save("IP_ADDRESS", ip_address)
    system.save("AP_IP_ADDRESS", ap_ip_address)
    system.save("DEBUG", debug)
    system.save("SDCARD", sdcard)
    system.save("WIFI", wifi)
    system.save("ESSID", essid)
    system.save("SMART", smart)
    system.save("CONNECTED", connected)
    system.save("RECONNECT", reconnect)
    system.save("AP", ap)
    system.save("AP_IF", ap_if)
    system.save("TIMESYNC", timesync)
    system.save("UTC", utc)
    system.save("RTC", rtc)
    system.save("RTC_MODUL", rtc_modul)

    if test:
        print("\n----- SYSTEM -----")
        for key in system.keys(): print("{}: {}".format(key, system.get(key)))


# init
init()

# run app
from app.app import main

#main()

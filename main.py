import gc
from core.database import Database

# main
print("main...")

def init():
    
    """
    Define db-files
    """
    BOOT_DATABASE = "/boot.db"
    SYSTEM_DATABASE = "/system.db"
    
    """
    Get init params from boot db-file
    Set default params as fallback
    """
    try:
        boot = Database(BOOT_DATABASE)
        init = boot.get("BOOT")
    except:
        print("boot config missing")
        init = {
            "DEBUG": False,
            "NETWORK": True,
            "SDCARD": False,
            "BLUETOOTH": False
        }
        boot = {
            "NETWORK":
            {
                "WIFI": False,
                "AP_IF": False,
                "AP": True
            }
        }
    
    """
    Default system params as fallback
    bool: mounted:   is SD-Card mounted
    bool: timesync:  is time sync
    bool: ap:        start Access Point
    bool: ap_if:     start Access Point, if wifi not connected
    bool: wifi:      use WiFi
    bool: rtc:       use rtc
    int:  utc:       set a timezone
    int:  reconnect: time for WiFi try-reconnecting loop 0=off
    """
    debug, mounted, wifi, connected, ap, ap_if, timesync, rtc = False, False, False, False, False, False, False, False
    ip_address, ap_ip_address = "0.0.0.0", "0.0.0.0"
    reconnect, utc = 0, 0
    
    """
    Debug modus
    """
    debug = init.get("DEBUG")
    
    if debug:
        """
        reset cause return codes
        0 Undefined
        1 Power reboot
        2 External reset or wake-up from Deep-sleep
        4 Hardware WDT reset
        -------------------------------------------
        wake reason: return codes
        0
        1
        2
        3
        4
        -------------------------------------------
        """
        from machine import reset_cause, wake_reason
        print("\n----- MACHINE -----")
        print("reset cause:", reset_cause())
        print("wake reason:", wake_reason())
        device = boot.get("DEVICE")
        if device is not None:
            print("\n----- DEVICE -----")
            for key, value in device.items():
                print("{}: {}".format(key, value))
    """
    TODO: find a better way...
    First try to mount SDCard
    Reset the board, if the device is busy (errno 16)
    After reset the SDCard will mount
    """
    if init.get("SDCARD"):
        from core.sdcard import mount
        mounted = mount(path=boot.get("SDCARD").get("PATH"), debug=debug)
    
    """
    Smart: trys to connect each network saved in network.db
    Default: connect to the default network saved in network.db or network.json
    """
    if init.get("NETWORK"):
        print("\nnetwork...")
        from core.wifi import smart_connect, connect, is_connected, get_ip, get_ap_ip, start_ap, stop_ap
        network = boot.get("NETWORK")
        ap_if = network.get("AP_IF")
        ap_start = False
        if network.get("WIFI"):
            stop_ap()
            wifi = True
            reconnect = network.get("RECONNECT")
            if network.get("SMART"): smart_connect()
            else: connect()
            if is_connected():
                connected = True
                ip = get_ip()
                if ip is not None: ip_address = ip
                """
                Timezone UTC+ to set an offset for the RTC
                """
                from timezone import Timezone
                timezone = boot.get("TIMEZONE")
                utc = timezone.get("UTC")
                if debug: print("TIMEZONE:", timezone.get("ZONE"))   
                """
                timeset by ntptime modul
                """
                try:
                    from ntptime import settime
                    settime()
                    Timezone(utc).offset()
                    timesync = True
                    print('time synchronized')
                except Exception as e:
                    print('setting time failed')
                """
                Fallback: timeset by online host
                """
                if not timesync:
                    try:
                        Timezone(utc).settime()
                        timesync = True
                        print('time synchronized in fallback')
                    except Exception as e:
                        print('setting time failed in fallback')
            elif ap_if:
                ap_start = True
        elif network.get("AP"):
            ap = ap_start = True
        if ap_start:
            start_ap()
            ip = get_ap_ip()
            if ip is not None: ap_ip_address = ip  
    """
    TODO:
    Sync time by RTC
    """    
    if not timesync and boot.get("RTC"):
        print("TODO: sync time by RTC modul...")
        print("MODUL:", boot.get("RTC").get("MODUL"))
        
    """
    Store states in db-file
    db-file is global accessable
    """
    system = Database(SYSTEM_DATABASE, create=True)
    system.save("IP_ADDRESS", ip_address)
    system.save("AP_IP_ADDRESS", ap_ip_address)
    system.save("DEBUG", debug)
    system.save("SDCARD", mounted)
    system.save("WIFI", wifi)
    system.save("CONNECTED", connected)
    system.save("RECONNECT", reconnect)
    system.save("AP", ap)
    system.save("AP_IF", ap_if)
    system.save("TIMESYNC", timesync)
    system.save("UTC", utc)
    system.save("RTC", rtc)
    
    if debug:
        print("\n----- SYSTEM -----")
        for key in system.keys(): print("{}: {}".format(key, system.get(key)))

# init
init()

# run app
from app.app import main
main()

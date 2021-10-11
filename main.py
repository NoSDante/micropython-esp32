import gc
from app.database import Database


# main
print("main...")

def init():
    
    """
    Define db-files
    """
    BOOT_DATABASE = "/boot.db"
    SYSTEM_DATABASE = "/system.db"
    
    """
    Initialize db-tree class
    Get init params from boot db-file
    """
    boot = Database(BOOT_DATABASE)
    init = boot.get("BOOT")
    
    """
    NOTE:
    Cannot initialize the system without config
    """
    if init is None:
        raise RuntimeError("boot config missing")
    
    """
    NOTE:
    Define default system params as fallback
    """
    debug, mounted, wifi, connected, ap, timesync, rtc = False, False, False, False, False, False, False
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
        from  esp32 import raw_temperature
        print("\n----- MACHINE -----")
        print("reset cause:", reset_cause())
        print("wake reason:", wake_reason())
        print("esp32 raw temperature: {} °C | {} °F".format((raw_temperature()-32)*5/9, raw_temperature()))
        device = boot.get("DEVICE")
        if device is not None:
            print("\n----- DEVICE -----")
            for key, value in device.items():
                print(key + ": " + str(value))
    """
    NOTE:
    First try to mount SDCard
    Reset the board, if the device is busy (errno 16)
    After reset the SDCard will mount
    """
    if init.get("SDCARD"):
        from sdcard import mount
        mounted = mount(path=boot.get("SDCARD").get("PATH"), debug=debug)
    
    """
    NOTE:
    Smart connect - trys to connect each network saved in network.db
    Default - connect to the default network saved in network.db or network.json
    """
    if init.get("NETWORK"):
        print("\nnetwork...")
        from wifi import smart_connect, connect, is_connected, get_ip, get_ap_ip, start_ap, stop_ap
        network = boot.get("NETWORK")
        if network.get("WIFI"):
            wifi = True
            reconnect = network.get("RECONNECT")
            if network.get("SMART"):
                smart_connect()
            else:
                connect()
        if network.get("AP") or (network.get("AP_IF") and not is_connected()):
            start_ap()
            ap = True
            ip = get_ap_ip()
            if ip is not None: ap_ip_address = ip
        else:
            stop_ap()
        
        if is_connected():
            connected = True
            ip = get_ip()
            if ip is not None: ip_address = ip
            """
            NOTE:
            Declare Timezone UTC+ to set an offset for the RTC
            """
            from timezone import Timezone
            timezone = boot.get("TIMEZONE")
            utc = timezone.get("UTC")
            if debug: print("TIMEZONE:", timezone.get("ZONE"))   
            """
            NOTE: Online connection neccessary
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
            NOTE: Online connection neccessary
            Backup timeset by online host
            """
            if not timesync:
                try:
                    Timezone(utc).settime()
                    timesync = True
                    print('time synchronized')
                except Exception as e:
                    print('setting time failed')
            
        elif boot.get("RTC"):
                print("TODO: sync time by RTC modul...")
                print("MODUL:", boot.get("RTC").get("MODUL"))
    
    """
    NOTE:
    Store states in db-file to controll system in process
    The db-file is global accessable for read- and writing
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
    system.save("TIMESYNC", timesync)
    system.save("UTC", utc)
    system.save("RTC", rtc)
    
    if debug:
        print("\n----- SYSTEM -----")
        keys = system.keys()
        for key in keys:
            value = system.get(key)
            print("{}: {}".format(key, value))
    
    # delete database objects
    del boot
    del system

# init
init()

# run app
from app.app import main
main()

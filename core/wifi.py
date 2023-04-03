from network import WLAN, STA_IF, AP_IF
from time import sleep_ms
from core.database import Database


def is_connected():
    """
    Check if the WLAN is connected to a network
    """
    wlan = WLAN(STA_IF)
    return wlan.active() and wlan.isconnected()

def get_config(file="network.json", path="/config/"):
    """
    Get wifi-config from JSON-File
    """
    if not isinstance(file, str): raise ValueError('file must be a string')
    if len(file) == 0: raise ValueError('file string is empty')
    import json
    with open(path+file) as json_data_file:
        return(json.load(json_data_file))

def get_network(database="/network.db", network="default"):
    """
    Get wifi-config from Database
    """
    if not isinstance(network, str): raise ValueError('network must be a string')
    if len(network) == 0: raise ValueError('network string is empty')
    return Database(database).get(network)

def get_mac():
    """
    Get the MAC address
    """
    mac = None
    wlan = WLAN(STA_IF)
    if not wlan.active(): wlan.active(True)
    import ubinascii
    mac = ubinascii.hexlify(wlan.config('mac'),':').decode()
    return mac

def get_ip():
    """
    Get the IP address for the current active WLAN
    """
    wlan = WLAN(STA_IF)
    if wlan.active() and wlan.isconnected(): details = wlan.ifconfig()
    return details[0] if details else None

def get_essid():
    """
    Get the ESSID for the current active WLAN
    """
    wlan = WLAN(STA_IF)
    if wlan.active() and wlan.isconnected(): essid = wlan.config('essid')
    return essid if essid else None

def get_ap_ip():
    """
    Get the IP address of the Access Point, if it is running
    """
    ap = WLAN(AP_IF)
    if ap.active(): details = ap.ifconfig()
    return details[0] if details else None

def get_ap_essid():
    """
    Get the ESSID for the Access Point
    """
    ap = WLAN(AP_IF)
    if ap.active(): essid = ap.config('essid')
    return essid if essid else None

def get_netscan():
    """
    Get the networks found in WLAN
    """    
    networks = []
    wlan = WLAN(STA_IF)
    if not wlan.active(): wlan.active(True)
    scans = wlan.scan()
    for scan in scans:
        networks.append(scan[0].decode())
        #print('found essid: ' + scan[0].decode())
    return networks

def smart_connect():
    database = Database(database="/network.db")
    networks = get_netscan()
    for key in database.keys():
        network = database.get(key)
        if network.get("essid") in networks:
            print("network found in wlan:", network.get("essid"))
            connect(network.get("essid"), network.get("password"))
            if is_connected():
                break

def connect(essid=None, password="", store=False):
    """
    Connect to the WiFi network based on the configuration.
    Fails silently if there is no configuration.
    """
    print('connecting...')

    # default
    static_ip = False
    cfg = None
    
    # load wifi-config if essid is None
    if essid is None:
        cfg = get_network()
        # fallback config from json-file
        if cfg is None: cfg = get_config()
        if cfg is None:
            print("no network config found")
            return
        # set wifi parameters from cfg
        essid = str.encode(cfg['essid']).decode()
        password = str.encode(cfg['password']).decode()
        static_ip = cfg['static_ip']
    else:
        # save network in db-file
        if store: save_network(essid, password)
    
    # get config by essid
    if password is None and cfg is None:
        cfg = get_network(network=essid)
        #if cfg is None: cfg = get_config()
        if cfg is None:
            print("no network config found")
            return        
        password = str.encode(cfg['password']).decode()
        static_ip = cfg['static_ip']
    
    # init WLAN
    wlan = WLAN(STA_IF)
    wlan.active(True)
    wlan_essid = str.encode(wlan.config('essid')).decode()
    
    # check if connection exists
    if wlan.isconnected() and (wlan_essid == essid):
        print('already connected with ' + essid)
        print('network:', wlan.ifconfig())
        return
    
    # set static ip parameters from wifi-config
    if static_ip:
        ip = str.encode(cfg['ip']).decode()
        subnet = str.encode(cfg['subnet']).decode()
        gateway = str.encode(cfg['gateway']).decode()
        dns = str.encode(cfg['dns']).decode()
        wlan.ifconfig(ip, subnet, gateway, dns)
    
    print('connecting to', essid, end='')
    try:
        wlan.connect(essid, password)
        for retry in range(20):
            connected = wlan.isconnected()
            if connected:
                print(' successfully connected')
                print('ip address:', wlan.ifconfig()[0])
                print('essid:', str.encode(wlan.config('essid')).decode())
                break
            sleep_ms(500)
            print('.', end='')
        if not connected:
            print(' connecting failed')        
            wlan.active(False)
    except Exception as e:
        # print error
        print(e)

def disconnect():
    """
    Disconnect network
    """
    print('disconnect from network')
    wlan = WLAN(STA_IF)
    if wlan.isconnected(): wlan.disconnect()
    wlan.active(False)

def start_ap(essid="ESP32-AP", password="0000", max_clients=5):
    """
    Set Access Point
    """
    print("start Access Point")
    try:
        ap = WLAN(AP_IF)
        if not ap.active(): ap.active(True)
        ap.config(essid=essid, password=password, max_clients=max_clients)
    except Exception as e:
        print(e)

def stop_ap():
    """
    Stop Access Point
    """
    print("stop Access Point")
    ap = WLAN(AP_IF)
    ap.active(False)

def save_network(essid, password, network=None):
    print("save network")
    if not network: network=essid
    Database(database="/network.db").save(network, {'essid': essid, 'password': password})

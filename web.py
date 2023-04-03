#from main import init
from core.database import Database
# MicroWebSrv2 libs
from MicroWebSrv2  import *


# App libs
from app.store import Store

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
    ip_address = system.get("IP_ADDRESS"),
    smart = system.get("SMART"),
    connected = system.get("CONNECTED"),
    ap = system.get("AP"),
    ap_if = system.get("AP_IF"),
    ap_ip_address = system.get("AP_IP_ADDRESS")
)

def start_web():
    print("\nloading config...")
    # load app config
    config = Database("/app/app.db")
    
    # I2C
    I2C_SLOT = config.get("I2C").get("SLOT")
    SDA_PIN  = config.get("I2C").get("SDA")
    SCL_PIN  = config.get("I2C").get("SCL")
    
    # WEBSOCKET
    WEB_INIT = config.get("WEB").get("INIT")
    WEB_ROOT = config.get("WEB").get("ROOT")
    
    print("\nwebsocket...")
    # Instanciates the MicroWebSrv2 class,
    mws2 = MicroWebSrv2()
    # SSL is not correctly supported on MicroPython.
    # But you can uncomment the following for standard Python.
    # mws2.EnableSSL( certFile = 'SSL-Cert/openhc2.crt',
    #                 keyFile  = 'SSL-Cert/openhc2.key' )
    # For embedded MicroPython, use a very light configuration,
    mws2.SetEmbeddedConfig()
    
    # Set Properties
    mws2.AllowAllOrigins = True
    mws2.CORSAllowAll = True
    
    # All pages not found will be redirected to the home '/',
    mws2.NotFoundURL = '/'
    # set the RootPath property for another directory for web file        
    if state.get("sdcard"): root="sd/"+WEB_ROOT
    else: root="www"
    if debug: print("Webserver Rootpath:", root)
    mws2.RootPath = root
    # set the BindAddress property to change the default server port or bind IP address
    IPAddress = None
    if state.get("ap_ip_address") != "0.0.0.0": IPAddress = state.get("ap_ip_address")
    if state.get("ip_address") != "0.0.0.0": IPAddress = state.get("ip_address")
    if debug: print("Webserver IP-Address:", IPAddress)
    if IPAddress: mws2.BindAddress = (IPAddress, 8080)
    # Starts the server as easily as possible in managed mode,
    mws2.StartManaged()
    
    @WebRoute(GET, '/server', name='SetServer)
    def SetHeaderServerName(microWebSrv2, request):
        request.Response.SetHeader("server", "MicroWebSrv2")
        request.Response.ReturnOkJSON({"server": "MicroWebSrv2"})

    @WebRoute(GET, '/reset', name='GetResetMachine')
    def ResponseResetMachine(microWebSrv2, request):
        from machine import reset
        request.Response.ReturnOkJSON({"success": "Machine ist restarting..."})
        reset()
        
    @WebRoute(GET, '/sensordata', name='GetSCD30SensorData')
    def ResponseGetSCD30SensorData(microWebSrv2, request):
        sensor = {
            'scd30': {
                'data':{
                    'co2': 520,
                    'co2_max': 1000,
                    'co2_min': 480,            
                    'temp': 22.2,
                    'temp_max': 23.7,
                    'temp_min': 19.2,
                    'relh': 40,
                    'relh_max': 48,
                    'relh_min': 37,
                    'error': 0
                    }
                }
            }
        try:
            if sensor:
                if hasattr(sensor, 'scd30'):
                    response = sensor.scd30.data
                    response.update({"success": "SCD30 data loaded"}) 
                    print(response)
                    response = "SCD30 data loaded"
                else:
                    response = {"error": "SCD30 delivers no data"}
            else:
                response = {"error": "SCD30 not present"}
        except Exception as e:
                response = "Exception {}".format(e)
        request.Response.ReturnOk(response)
        
    @WebRoute(GET, '/bootconfig', name='GetBootConfig')
    def ResponseBootConfig(microWebSrv2, request):
        #request.Response.AccessControlAllowOrigin = "Access-Control-Allow-Origin: *"
        from os import listdir
        try:
            if "boot.json" in listdir("config"):
                response = system.get_json_data("boot.json", path="config/")
                response.update({"success": "Bootconfig loaded!"})
            else:
                response = {"info": "Bootconfig doesn't exist!"}
        except Exception as e:
            msg = ("Could not load bootfile", e)
            response = {"error": msg}
        request.Response.ReturnOkJSON(response)
        
    @WebRoute(GET, '/systemstate', name='GetSystemState')
    def ResponseSystemState(microWebSrv2, request):
        #request.Response.AccessControlAllowOrigin = "Access-Control-Allow-Origin: *"
        from os import listdir
        try:
            if "system.db" in listdir():
                response = system.get()
                response.update({"success": "Systemstates loaded!"})
            else:
                response = {"info": "Systemstates don't exist!"}
        except Exception as e:
            msg = ("Could not read systemstate", e)
            response = {"error": msg}
        request.Response.ReturnOkJSON(response)    
        
    @WebRoute(GET, '/resetbootfile', name='GetResetBootFile')
    def ResponseResetBootConfig(microWebSrv2, request):
        from os import remove, listdir
        try:
            if "boot.db" in listdir():
                remove("boot.db")
                response = {"success": "Bootfile deleted!<br><p>Restart to Setup</p"}
            else:
                response = {"success": "Bootfile does not exist!"}
        except Exception as e:
            msg = ("Could not reset bootfile", e)
            response = {"error": msg}
        request.Response.ReturnOkJSON(response)
        
    @WebRoute(POST, '/savebootconfig', name='PostBootConfig')
    def RequestBootConfig(microWebSrv2, request):
        data = request.GetPostedJSONObject()
        #if debug: print("POST-RAW:", data)
        if debug: print("POST-LENGTH:", len(data))
        if debug: print("POST-TYPE:", type(data))
        if data:
            from os import remove
            try:
                data = str(data)
                data = data.replace("'","\"")
                data = data.replace("False","false")
                data = data.replace("True","true")
                with open('config/boot.json', 'w+b') as file:
                    file.write(data)                
                    response = system.get_json_data("boot.json", path="config/")
                    response.update({"success": "Bootconfig saved!"})
            except Exception as e:
                msg = ("Could not create bootconfig", e)
                response = {"error": msg}
        else:
            response = {"error": "data is {}".format(type(data))}
        if debug: print("Response:", response)
        request.Response.ReturnOkJSON(response)


# run websocket
#init()

if __name__ == '__main__':
    try:
        start_web()
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt')
from microWebSrv import MicroWebSrv
from machine import Pin
from dht import DHT22

sensor = DHT22(Pin(15, Pin.IN, Pin.PULL_UP))   # DHT-22 on GPIO 15

def _httpHandlerDHTGet(httpClient, httpResponse):
    try:
        sensor.measure()   # Poll sensor
        t, h = sensor.temperature(), sensor.humidity()
        if all(isinstance(i, float) for i in [t, h]):   # Confirm values
            data = '{0:.1f}&deg;C {1:.1f}%'.format(t, h)
        else:
            data = 'Invalid reading.'
    except:
        data = 'Attempting to read sensor...'
        
    httpResponse.WriteResponseOk(
        headers = ({'Cache-Control': 'no-cache'}),
        contentType = 'text/event-stream',
        contentCharset = 'UTF-8',
        content = 'data: {0}\n\n'.format(data) )

routeHandlers = [ ( "/dht", "GET",  _httpHandlerDHTGet ) ]
srv = MicroWebSrv(routeHandlers=routeHandlers, webPath='/www/')
srv.Start(threaded=False)

import machine, time
    
class Timezone():

    HOST = "pool.ntp.org"
    NTP_DELTA = 3155673600
    
    def __init__(self, utc=0):
        if not isinstance(utc, int): raise ValueError('UTC must be an integer')
        self.utc = utc
        
    def gettime(self):
        import usocket as socket
        import ustruct as struct
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(self.HOST, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        t = struct.unpack("!I", msg[40:44])[0]
        return t

    # There's currently no timezone support in MicroPython, and the RTC is set in UTC time.
    def offset(self):
        # UTC+2 Mitteleuropäische Sommerzeit
        TZ_OFFSET = 3600 * self.utc
        t = time.mktime(time.localtime())
        t = t + TZ_OFFSET
        tm = time.gmtime(t)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    
    def settime(self):
        TZ_OFFSET = 3600 * self.utc
        t = self.gettime() - self.NTP_DELTA + TZ_OFFSET
        tm = time.gmtime(t)
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

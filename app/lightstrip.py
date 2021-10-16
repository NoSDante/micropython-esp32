import uasyncio as asyncio
from neopixel import NeoPixel
from time import sleep_ms


class Lightstrip():
    
    class PixelRangeException(Exception):
        pass
    
    def __init__(self, pin_neo=None, pixel=None):
        self.neopixel = NeoPixel(pin_neo, pixel)
        self.n = pixel if not pixel else self.neopixel.n
        if self.n not in range(0, self.neopixel.n): self.n = self.neopixel.n     
        self.clear()
    
    # light all
    def color(self, color="WHITE"):
        for i in range(self.n): self.neopixel[i] = (self.rgb(color))
        self.neopixel.write()
        
    # light one
    def pixel(self, pixel, color="WHITE"):
        if pixel not in range(0, self.n): raise self.PixelRangeException("pixel is out of range")
        self.neopixel[pixel] = (self.rgb(color))
        self.neopixel.write()
    
    # light each
    def each(self, each, color="WHITE", clear=True):
        for i in range(self.n):
            if ((i+each) % 2) == 0: self.neopixel[i] = (self.rgb(color))
        self.neopixel.write()
        if clear: self.clear()
    
    # bounce all
    async def bounce(self, color="WHITE", wait=120, clear=True):
        for i in range(4 * self.n):
            for j in range(self.n): self.neopixel[j] = (self.rgb(color))
            if (i // self.n) % 2 == 0: self.neopixel[i % self.n] = (0, 0, 0)
            else: self.neopixel[self.n - 1 - (i % self.n)] = (0, 0, 0)
            self.neopixel.write()
            await asyncio.sleep_ms(wait)
        if clear: self.clear()
    
    # clear pixels
    def clear(self):
        for i in range(self.n): self.neopixel[i] = (0, 0, 0)
        self.neopixel.write()
    
    # fade in/out    
    async def fade(self, wait=60, clear=True):
        for i in range(0, 4 * 256, 8):
            for j in range(self.n):
                if (i // 256) % 2 == 0: val = i & 0xff
                else: val = 255 - (i & 0xff)
                self.neopixel[j] = (val, 0, 0)
            self.neopixel.write()
        await asyncio.sleep_ms(wait)
        if clear: self.clear()
    
    # cycle rtl
    async def cycle(self, color="WHITE", times=1, wait=60, clear=True):
        for i in range(times * self.n):
            for j in range(self.n): self.neopixel[j] = (0, 0, 0)
            self.neopixel[i % self.n] = (self.rgb(color))
            self.neopixel.write()
            await asyncio.sleep_ms(wait)
        if clear: self.clear()
    
    # rgb color collection
    def rgb(self, color):
        default = "WHITE"        
        colors = {
            "RED"           : ( 255,  10,  10 ),
            "GREEN"         : (   0, 128,   0 ),
            "WHITE"         : ( 255, 255, 255 ),
            "BLACK"         : (   0,   0,   0 ),
            "YELLOW"        : ( 225, 255,   0 ),
            "CYAN"          : (   0, 255, 255 ),
            "LIME"          : (   0, 255,   0 ),
            "YELLOW GREEN"  : ( 154, 205,  50 ),
            "YELLOW"        : ( 225, 255,   0 ),
            "DARK ORANGE"   : ( 255, 140,   0 ),
            "ORANGE"        : ( 255, 165,   0 ),
            "DEEP SKY BLUE" : (   0, 191, 255 ),                
            "MEDIUM BLUE"   : (   0,   0,  205),
            "BLUE"          : (   0,   0,  255),
            "ORANGE RED"    : ( 255,  69,    0)
        }
        if not color in colors:
            print("color '{}' does not exist").format(color)
            color = default
        r = colors[color][0]
        g = colors[color][1]
        b = colors[color][2]
        return r, g, b

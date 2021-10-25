from machine import SPI, Pin


class Display(object):
    
    class FontNotDefined(Exception):
        pass

    BAUDRATE = 40000000
    
    def __init__(self, slot=2, sck=18, mosi=23, miso=19, cs=5, dc=26, reset=25, led=None, width=240, height=320, rotation=0): 
        self.display = None
        self.font = None
        
        try:
            from tft.ili9341 import Display, color565
            self.color565 = color565
            # hardware SPI, HSPI
            spi = SPI(slot, baudrate=self.BAUDRATE, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
            self.display = Display(spi, dc=Pin(dc), cs=Pin(cs), rst=Pin(reset), width=width, height=height, rotation=rotation)
            # set a Pin to power on/off the display
            if led is not None:
                self.tft.power = Pin(led, Pin.OUT, value=1)
        except OSError as e:
            raise OSError('cannot not initialize SPI bus! ', e)
    
    """FONT
    Set font for drawing text
    Set font width, height to calculate coords
    """
    def setFont(self, font='Espresso_Dolce18x24.c', w=18, h=24):
        from tft.xglcd_font import XglcdFont
        self.font = XglcdFont(font, w, h)
        self.font_width = w
        self.font_height = h
    
    """RGB
    Get rgb values from a color
    Return a default value, if color not exists
    """
    def rgb(self, color):
        default = "WHITE"
        colors = {
            "RED"           : (255,  10,  10),
            "GREEN"         : (  0, 128,   0),
            "WHITE"         : (255, 255, 255),
            "BLACK"         : (  0,   0,   0),
            "CYAN"          : (  0, 255, 255),
            "LIGHT CYAN"    : (224, 255, 255),
            "AQUA MARINE"   : (127, 255, 212),
            "LIME"          : (  0, 255,   0),
            "YELLOW GREEN"  : (154, 205,  50),
            "YELLOW"        : (225, 255,   0),
            "DARK ORANGE"   : (255, 140,   0),
            "ORANGE"        : (255, 165,   0),
            "DEEP SKY BLUE" : (  0, 191, 255),            
            "MEDIUM BLUE"   : (  0,   0, 205),
            "BLUE"          : (  0,   0, 255),
            "ORANGE RED"    : (255,  69,   0),
            "GRAY"          : (128, 128, 128)
        }
        if not color in colors:
            #raise ValueError("rgb color does not exist")
            print("color '{}' does not exist").format(color)
            color = default
        r = colors[color][0]
        g = colors[color][1]
        b = colors[color][2]
        return r, g, b
    
    """DRAWING
    NOTE: Writing shorter code, when using display driver functions
    Not necessary to set the Font every time
    Only set a declared color from the rgb color collection
    """
    def draw_text(self, x, y, text, color="WHITE"):
        if not self.font: raise self.FontNotDefined("a font is not defined")
        self.display.draw_text(x, y, text, self.font, self.color(color))

    def draw_rectangle(self, x, y, w, h, color="WHITE"):
        self.display.draw_rectangle(x, y, w, h, self.color(color))
        
    # function rgb, color565
    def color(self, color):
        r, g, b = self.rgb(color)
        return self.color565(r, g, b)

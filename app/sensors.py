import uasyncio as asyncio
from machine import Pin, I2C, UART
from time import sleep

class Sensors():
    
    I2C_SLOT = 1
    I2C_SDA  = 21
    I2C_SCL  = 22
    I2C_FREQ = 400000
    
    IMPORT_ERROR = "cannot import module"
    I2C_ERROR = "cannot initialize I2C"
    UART_ERROR = "cannot initialize UART"
    
    def __init__(self, i2c=None, debug=False):
        self.debug = debug
        self.i2c = None
        self.uart = None
        if isinstance(i2c, I2C): self.i2c = i2c
        else: self.init_I2C()
    
    def init_I2C(self):
        try:            
            self.i2c = I2C(self.I2C_SLOT, scl=Pin(self.I2C_SCL), sda=Pin(self.I2C_SDA), freq=self.I2C_FREQ)
            #self.i2c = I2C(self.I2C_SLOT)
            if self.debug: print("\n----- I2C -----\n", self.i2c)
        except Exception as e:
            raise Exception(self.I2C_ERROR, e)
    
    def init_BH1750(self, i2c=None):        
        self.bh1750 = None
        try: from lib.bh1750 import BH1750
        except ImportError as e:
            print(self.IMPORT_ERROR, e)
        if isinstance(i2c, I2C): self.i2c = i2c
        self.bh1750 = BH1750(self.i2c)
        self.bh1750.data = {}

    def init_SPS30(self, port=1, rx=9, tx=10, start=True, clean=True, sample=60):
        self.sps30 = None
        
        try: from lib.sps30 import SPS30
        except ImportError as e:
            print(self.IMPORT_ERROR, e)
        
        try:
            self.sps30 = SPS30(port=UART(port, baudrate=115200, bits=8, parity=None, stop=1, rx=rx, tx=tx), debug=self.debug, sample=sample)
        except Exception as e:
            print(self.UART_ERROR, e)
        
        self.sps30.Standby(debug=self.debug)
        
        if self.debug: print("\n----- SPS30 -----\n", self.sps30.device_info(debug=self.debug))
        
        self.sps30.data = {}
        self.sps30.ready = True
        if clean: self.sps30.fan_clean(debug=self.debug)
        if start: self.sps30.start_measurement(debug=self.debug)
            
    def init_SCD30(self, i2c=None, start=True, pause=1000):        
        self.scd30 = None
        
        try: from lib.scd30 import SCD30
        except Exception as e:
            print(self.IMPORT_ERROR, e)
            
        if isinstance(i2c, I2C): self.i2c = i2c
        
        #I2C address
        SCD30_I2C_ADDR = 0x61

        try:
            self.scd30 = SCD30(self.i2c, SCD30_I2C_ADDR, pause=pause)
        except Exception as e:
            print(self.I2C_ERROR, e)
        
        self.scd30.data = {}
        self.scd30.started = False
        self.scd30.ready = True

        if start:
            self.scd30.start_continous_measurement()
            self.scd30.started = True
        
        if self.debug:
            print("\n----- SCD30 -----")
            print("Firmware: {}".format(self.scd30.get_firmware_version()))
            print("Forced Recalibration: {}ppm".format(self.scd30.get_forced_recalibration()))
            print("Automatic Recalibration: {}".format(self.scd30.get_automatic_recalibration()))
            print("Measurement Interval: {}sec".format(self.scd30.get_measurement_interval()))
            print("Temperature Offset: {} ".format(self.scd30.get_temperature_offset()))
            print("Altitude Comp: {}".format(self.scd30.get_altitude_comp()))
      
    async def init_AS3935(self, i2c=None, pin_irq=None, capacitance=120, indoor=True, disturber=True):
        self.as3935 = None
        
        try: from lib.DFRobot_AS3935_Lib import DFRobot_AS3935
        except ImportError as e:
            print(self.IMPORT_ERROR, e)
        
        #I2C address
        #AS3935_I2C_ADDR1 = 0X01
        #AS3935_I2C_ADDR2 = 0X02
        #AS3935_I2C_ADDR3 = 0X03
        AS3935_I2C_ADDR = [0X01,0X02,0X03]
        AS3935_I2C_FREQ  = 400000
                
        if isinstance(i2c, I2C): self.i2c = i2c
        
        for addr in AS3935_I2C_ADDR:
            if self.debug: print("initializing as3935 with I2C address", hex(addr))
            for retry in range(10):
                self.as3935 = DFRobot_AS3935(addr, self.i2c)
                if self.as3935.reset():
                    break
                if self.debug: print("error initializing as3935", retry)
                asyncio.sleep(0.5)
                
        if not self.as3935.reset():
            self.as3935 = None
            return
        
        self.as3935.data = {}
        
        # configure sensor
        self.as3935.powerUp()

        # set indoors or outdoors models
        if indoor:
            self.as3935.setIndoors()
        else:
            self.as3935.setOutdoors()

        # disturber detection
        if disturber:
            self.as3935.disturberEn()
        else:
            self.as3935.disturberDis()

        self.as3935.setIrqOutputSource(0)
        asyncio.sleep(0.5)
        
        # set capacitance
        self.as3935.setTuningCaps(capacitance)

        # Connect the IRQ and GND pin to the oscilloscope.
        # uncomment the following sentences to fine tune the antenna for better performance.
        # This will dispaly the antenna's resonance frequency/16 on IRQ pin (The resonance frequency will be divided by 16 on this pin)
        # Tuning AS3935_CAPACITANCE to make the frequency within 500/16 kHz plus 3.5% to 500/16 kHz minus 3.5%
        #
        # self.as3935.setLcoFdiv(0)
        # self.as3935.setIrqOutputSource(3)

        # Set the noise level,use a default value greater than 7
        self.as3935.setNoiseFloorLv1(2)
        #noiseLv = self.as3935.getNoiseFloorLv1()

        # used to modify WDTH,alues should only be between 0x00 and 0x0F (0 and 7)
        self.as3935.setWatchdogThreshold(2)
        #wtdgThreshold = self.as3935.getWatchdogThreshold()

        # used to modify SREJ (spike rejection),values should only be between 0x00 and 0x0F (0 and 7)
        self.as3935.setSpikeRejection(2)
        #spikeRejection = self.as3935.getSpikeRejection()
        
        self.as3935.trigger = pin_irq

        # view all register data
        if self.debug: self.as3935.printAllRegs()
    
    def init_MQ2(self, pin_analog=None, pin_trigger=None, baseVoltage=5.0, interval=2, calibrate=True):
        
        self.mq2 = None
       
        if pin_analog is None: raise ValueError('analog pin is not defined')
        
        try: from lib.MQ2 import MQ2
        except ImportError as e:
            print(self.IMPORT_ERROR, e)
        
        ## This strategy measure values immideatly, so it might be inaccurate. Should be
        #  suitable for tracking dynamics, raither than actual values    
        STRATEGY_FAST = const(1)
        
        ## This strategy measure values separatelly. For a single measurement
        #    MQ_SAMPLE_TIMES measurements are taken in interval MQ_SAMPLE_INTERVAL.
        #    I.e. for multi-data sensors, like MQ2 it would take a while to receive full data
        STRATEGY_ACCURATE = const(2)
        
        self.mq2 = MQ2(pinData=pin_analog, baseVoltage=baseVoltage, measuringStrategy=STRATEGY_FAST)
        self.mq2.calibration = False
        self.mq2.data = {}

        # Calibration default sampletime 5000ms x (5)
        if calibrate:
            self.mq2.calibrate()
            self.mq2.calibration = True
        
        ## Set digital out of MQ2 as trigger
        # A low level signal triggers a gas detection => trigger.value() == 0
        self.mq2.trigger = pin_trigger

        if self.debug:
            print("\n----- MQ2 -----")
            print("Calibrated: {}".format(self.mq2.calibration))
            print("Base resistance: {}".format(self.mq2._ro))
            print("Bas Voltage: {}".format(baseVoltage))
            print("Pin Analog data: {}".format(pin_analog))
            print("Pin Digital trigger: {}".format(pin_trigger))

class Scoring(object):
    
    DEFAULT_VALUE = "DEFAULT"
    
    def __init__(self, debug=False):
        self.debug = debug
    
    def co2(self, value):
        score = None
        if value is None: return score
        if value in range(0, 600):
            score = "GREAT"
        if value in range(600, 800):
            score = "GOOD"
        if value in range(800, 1000):
            score = "NORMAL"
        if value in range(1000, 1200):
            score = "BAD"
        if value in range(1200, 1600):
            score = "VERY BAD"
        if value in range(1600, 2000):
            score = "CRITICAL"    
        if value >= 2000:
            score = "DANGER"
        return score
    
    def temperature(self, value):
        score = None
        if value is None: return score
        if value <= 0: score = "FREEZE"
        return score
    
    def heatindex(self, temp, hum):
        if temp is None or hum is None: return temp, status
        # Convert celcius to fahrenheit
        fahrenheit = ((temp * 9/5) + 32)
        hi, score = None, None
        if fahrenheit >= 80 and hum >= 40:
            # Creating multiples of 'fahrenheit' & 'hum' values for the coefficients
            T2 = pow(fahrenheit, 2)
            T3 = pow(fahrenheit, 3)
            H2 = pow(hum, 2)
            H3 = pow(hum, 3)
            # Coefficients for the calculations
            C1 = [ -42.379, 2.04901523, 10.14333127, -0.22475541, -6.83783e-03, -5.481717e-02, 1.22874e-03, 8.5282e-04, -1.99e-06]
            C2 = [ 0.363445176, 0.988622465, 4.777114035, -0.114037667, -0.000850208, -0.020716198, 0.000687678, 0.000274954, 0]
            C3 = [ 16.923, 0.185212, 5.37941, -0.100254, 0.00941695, 0.00728898, 0.000345372, -0.000814971, 0.0000102102, -0.000038646, 0.0000291583, 0.00000142721, 0.000000197483, -0.0000000218429, 0.000000000843296, -0.0000000000481975]
            # Calculating heat-indexes with 3 different formula
            heatindex1 = C1[0] + (C1[1] * fahrenheit) + (C1[2] * hum) + (C1[3] * fahrenheit * hum) + (C1[4] * T2) + (C1[5] * H2) + (C1[6] * T2 * hum) + (C1[7] * fahrenheit * H2) + (C1[8] * T2 * H2)
            heatindex2 = C2[0] + (C2[1] * fahrenheit) + (C2[2] * hum) + (C2[3] * fahrenheit * hum) + (C2[4] * T2) + (C2[5] * H2) + (C2[6] * T2 * hum) + (C2[7] * fahrenheit * H2) + (C2[8] * T2 * H2)
            heatindex3 = C3[0] + (C3[1] * fahrenheit) + (C3[2] * hum) + (C3[3] * fahrenheit * hum) + (C3[4] * T2) + (C3[5] * H2) + (C3[6] * T2 * hum) + (C3[7] * fahrenheit * H2) + (C3[8] * T2 * H2) + (C3[9] * T3) + (C3[10] * H3) + (C3[11] * T3 * hum) + (C3[12] * fahrenheit * H3) + (C3[13] * T3 * H2) + (C3[14] * T2 * H3) + (C3[15] * T3 * H3)
            hi = round(((((heatindex1+heatindex2+heatindex3)//3) - 32) * 5/9), 1)
        # score
        if hi:
            if hi in range(27, 32):
                score = "CAUTION"
            if hi in range(32, 41):
                score = "CRITCAL"
            if hi in range(41, 54):
                score = "DANGER"
            if hi >= 54:
                score = "EXTREME"               
        return hi, score
    
    def humidity(self, value):
        score = None
        return score
    
    def dust(self, value):
        score = None
        return score
    
    def color(self, value):
        colors = {
                "EXCELLENT" : ("GREEN"),
                "GREAT"     : ("GREEN"),
                "GOOD"      : ("LIME"),
                "NORMAL"    : ("YELLOW GREEN"),
                "BAD"       : ("YELLOW"),
                "VERY BAD"  : ("ORANGE"),
                "CAUTION"   : ("DARK ORANGE"),               
                "DANGER"    : ("RED"),
                "EXTREME"   : ("RED"),
                "CRITICAL"  : ("ORANGE RED"),
                "HOT"       : ("ORANGE"),
                "WARM"      : ("YELLOW"),
                "FAIR"      : ("DEEP SKY BLUE"),            
                "COLD"      : ("MEDIUM BLUE"),
                "FREEZE"    : ("BLUE"),
                "DEFAULT"   : ("WHITE"),          
                "UNKNOWN"   : ("ORANGE RED")
            }
        if not value in colors:
            value = self.DEFAULT_VALUE
            if self.debug: print("score color '{}' does not exist".format(value))
        return colors[value]

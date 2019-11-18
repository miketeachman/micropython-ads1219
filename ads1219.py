# The MIT License (MIT)
# Copyright (c) 2019 Mike Teachman
# https://opensource.org/licenses/MIT

# MicroPython driver for the Texas Instruments ADS1219 ADC

from micropython import const
import ustruct 
import utime

_CHANNEL_MASK = const(0b11100000)
_GAIN_MASK = const(0b00010000)
_DR_MASK = const(0b00001100)
_CM_MASK = const(0b00000010)
_VREF_MASK = const(0b00000001)

_COMMAND_RESET = const(0b00000110)
_COMMAND_START_SYNC = const(0b00001000)
_COMMAND_POWERDOWN = const(0b00000010)
_COMMAND_RDATA = const(0b00010000)
_COMMAND_RREG_CONFIG = const(0b00100000)
_COMMAND_RREG_STATUS = const(0b00100100)
_COMMAND_WREG_CONFIG = const(0b01000000)

_DRDY_MASK = const(0b10000000)  
_DRDY_NO_NEW_RESULT = const(0b00000000)    # No new conversion result available
_DRDY_NEW_RESULT_READY = const(0b10000000) # New conversion result ready

class ADS1219:
    CHANNEL_AIN0_AIN1 = const(0b00000000)  # Differential P = AIN0, N = AIN1 (default)
    CHANNEL_AIN2_AIN3 = const(0b00100000)  # Differential P = AIN2, N = AIN3
    CHANNEL_AIN1_AIN2 = const(0b01000000)  # Differential P = AIN1, N = AIN
    CHANNEL_AIN0 = const(0b01100000)       # Single-ended AIN0
    CHANNEL_AIN1 = const(0b10000000)       # Single-ended AIN1
    CHANNEL_AIN2 = const(0b10100000)       # Single-ended AIN2
    CHANNEL_AIN3 = const(0b11000000)       # Single-ended AIN3
    CHANNEL_MID_AVDD = const(0b11100000)   # Mid-supply   P = AVDD/2, N = AVDD/2
    
    GAIN_1X = const(0b00000) # Gain = 1 (default)
    GAIN_4X = const(0b10000) # Gain = 4
    
    DR_20_SPS = const(0b0000)   # Data rate = 20 SPS (default)
    DR_90_SPS = const(0b0100)   # Data rate = 90 SPS
    DR_330_SPS = const(0b1000)  # Data rate = 330 SPS
    DR_1000_SPS = const(0b1100) # Data rate = 1000 SPS

    CM_SINGLE = const(0b00)     # Single-shot conversion mode (default)
    CM_CONTINUOUS = const(0b10) # Continuous conversion mode

    VREF_INTERNAL = const(0b0) # Internal 2.048V reference (default)
    VREF_EXTERNAL = const(0b1) # External reference
    
    VREF_INTERNAL_MV = 2048 # Internal reference voltage = 2048 mV
    POSITIVE_CODE_RANGE = 0x7FFFFF # 23 bits of positive range    

    def __init__(self, i2c, address=0x40):
        self._i2c = i2c
        self._address = address
        self.reset()
                
    def _read_modify_write_config(self, mask, value):
        as_is = self.read_config()
        to_be = (as_is & ~mask) | value 
        wreg = ustruct.pack('BB', _COMMAND_WREG_CONFIG, to_be)
        self._i2c.writeto(self._address, wreg)
        
    def read_config(self):
        rreg = ustruct.pack('B', _COMMAND_RREG_CONFIG) 
        self._i2c.writeto(self._address, rreg)
        config = self._i2c.readfrom(self._address, 1)
        return config[0]
    
    def read_status(self):
        rreg = ustruct.pack('B', _COMMAND_RREG_STATUS) 
        self._i2c.writeto(self._address, rreg)
        status = self._i2c.readfrom(self._address, 1)
        return status[0]

    def set_channel(self, channel):
        self._read_modify_write_config(_CHANNEL_MASK, channel)
        
    def set_gain(self, gain):
        self._read_modify_write_config(_GAIN_MASK, gain)
        
    def set_data_rate(self, dr):
        self._read_modify_write_config(_DR_MASK, dr)
        
    def set_conversion_mode(self, cm):
        self._read_modify_write_config(_CM_MASK, cm)
        
    def set_vref(self, vref):
        self._read_modify_write_config(_VREF_MASK, vref)
        
    def read_data(self):
        if ((self.read_config() & _CM_MASK) == CM_SINGLE):
            self.start_sync()
            # loop until conversion is completed
            while((self.read_status() & _DRDY_MASK) == _DRDY_NO_NEW_RESULT):
                utime.sleep_us(100)        
            
        rreg = ustruct.pack('B', _COMMAND_RDATA) 
        self._i2c.writeto(self._address, rreg)
        data = self._i2c.readfrom(self._address, 3)
        return ustruct.unpack('>I', b'\x00' + data)[0]
    
    def read_data_irq(self):
        rreg = ustruct.pack('B', _COMMAND_RDATA) 
        self._i2c.writeto(self._address, rreg)
        data = self._i2c.readfrom(self._address, 3)
        return ustruct.unpack('>I', b'\x00' + data)[0]
        
    def reset(self):
        data = ustruct.pack('B', _COMMAND_RESET)
        self._i2c.writeto(self._address, data)  

    def start_sync(self):
        data = ustruct.pack('B', _COMMAND_START_SYNC)
        self._i2c.writeto(self._address, data)        

    def powerdown(self):
        data = ustruct.pack('B', _COMMAND_POWERDOWN)
        self._i2c.writeto(self._address, data)
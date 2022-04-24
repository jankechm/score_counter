# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

import app.constants as const
from app.display import Matrix
from app.clock import RTC
from app.memory import EEPROM
from machine import Pin, SPI, I2C

#########################################################################
# These 3 objects - RTC, EEPROM and Matrix - are used in many modules.
# It makes no sense to have more than 1 instance of each of them
# - there's just 1 piece of HW.
# That's the reason for this separate module - any other module
# can import this module and get access to these instances as singletons.
#########################################################################

# Real Time Clock & EEPROM config - same I2C bus
rtc_mem_i2c = I2C(const.RTC_I2C_ID, sda=Pin(const.RTC_I2C_SDA_PIN, Pin.OPEN_DRAIN),
	scl=Pin(const.RTC_I2C_SCL_PIN, Pin.OPEN_DRAIN), freq=400_000)

# Display config 
mx_spi = SPI(const.DISPLAY_SPI_ID, baudrate=const.DISPLAY_SPI_BAUD,
	polarity=const.DISPLAY_SPI_POLARITY, phase=const.DISPLAY_SPI_PHASE,
	sck=Pin(const.DISPLAY_SPI_CLK_PIN),
	mosi=Pin(const.DISPLAY_SPI_MOSI_PIN))
cs_pin = Pin(const.DISPLAY_SPI_CS_PIN, Pin.OUT)

####################################################
# 3 above mentioned objects representing HW modules.
####################################################

# Realt Time Clock
rtc = RTC(rtc_mem_i2c)
# Non-volatile memory
nv_mem = EEPROM(rtc_mem_i2c)
# LED matrix
display = Matrix(mx_spi, cs_pin, nv_mem.get_cfg().bright_lvl)
# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

########################
# Bit operations
########################
ONE_NIBBLE = 4
ONE_BYTE = 8
HIGHER_NIBBLE_MASK = 0XF0
LOWER_NIBBLE_MASK = 0X0F

########################
# Matrixes
########################
ROWS_IN_MATRIX = 8
COLS_IN_MATRIX = 8
CASCADED_MATRIXES = 8
MATRIXES_IN_ROW = 4
MATRIXES_IN_COL = 2

########################
# Offsets
########################
ONE_DIGIT_X_OFFSET = 4
ONE_DIGIT_IS_1_X_OFFSET = 7
FIRST_DIGIT_X_OFFSET = 2
SECOND_DIGIT_X_OFFSET = 6
SECOND_DIGIT_MEDIUM_FONT_X_OFFSET = 8
SECOND_DIGIT_IS_1_X_OFFSET = 12
RIGHT_SIDE_X_OFFSET = 16
RIGHT_SIDE_MEDIUM_FONT_X_OFFSET = 18

########################
# MAX7291 registers
########################
NOOP = 0x00
DECODEMODE = 0x09
INTENSITY = 0x0A
SCANLIMIT = 0x0B
SHUTDOWN = 0x0C
DISPLAYTEST = 0x0F

########################
# MAX7291 register values
########################
SHUTDOWN_MODE_ON = 0X00
SHUTDOWN_MODE_OFF = 0X01
DISPLAY_TEST_ON = 0X01
DISPLAYTEST_TEST_OFF = 0X00
SCANLIMIT_8_DIGITS = 0X07
NO_BCD_DECODE = 0X00
INITIAL_BRIGHTNESS = 0X01
ROW0 = 0x01

########################
# SPI & I2C
########################
DISPLAY_SPI_ID = 1
DISPLAY_SPI_BAUD = 5_000_000
DISPLAY_SPI_POLARITY = 1
DISPLAY_SPI_PHASE = 0

RTC_I2C_ID = 1

########################
# Pins
########################
RTC_I2C_SDA_PIN = 26
RTC_I2C_SCL_PIN = 27

DISPLAY_SPI_CS_PIN = 13
DISPLAY_SPI_CLK_PIN = 14
DISPLAY_SPI_MOSI_PIN = 15

RECV_PIN = 28

########################
# Buttons
########################
BUTTON_0 = 0X19
BUTTON_1 = 0X45
BUTTON_2 = 0X46
BUTTON_3 = 0X47
BUTTON_4 = 0X44
BUTTON_5 = 0X40
BUTTON_6 = 0X43
BUTTON_7 = 0X07
BUTTON_8 = 0X15
BUTTON_9 = 0X09

BUTTON_STAR = 0X16
BUTTON_HASH = 0X0D
BUTTON_OK = 0X1C

BUTTON_UP = 0X18
BUTTON_DOWN = 0X52
BUTTON_LEFT = 0X08
BUTTON_RIGHT = 0X5A

########################
# Halves & quarters
########################
LEFT = 1
RIGHT = 2

TOP_ROW = 1
BOTTOM_ROW = 2

TOP_LEFT = 1
TOP_RIGHT = 2
BOTTOM_LEFT = 3
BOTTOM_RIGHT = 4

########################
# RTC module
########################
DS3231_I2C_ADDR = 0x68

SECONDS_MEM_ADDR = 0
MINUTES_MEM_ADDR = 1
HOURS_MEM_ADDR = 2
WEEKDAY_MEM_ADDR = 3
DATE_MEM_ADDR = 4
MONTH_MEM_ADDR = 5
YEAR_MEM_ADDR = 6
DATE_TIME_REGS_NUM = 7

########################
# EEPROM module
########################
AT24C32_I2C_ADDR = 0x57

CFG_ADDR = 0X000
LAST_SCORE_ADDR = 0X00A

SCROLL_CFG_MASK = 0X01
USE_TIME_CFG_MASK = 0X02
USE_DATE_CFG_MASK = 0X04
USE_TEMPERATURE_CFG_MASK = 0X08
BRIGHT_LVL_CFG_MASK = 0XF0

LEFT_SCORE_MASK = 0XF0
RIGHT_SCORE_MASK = 0X0F

BRIGHT_LVL_BIT_SHIFT = 4
LEFT_SCORE_BIT_SHIFT = 4

########################
# Date & time
########################
DEC_BASE = 10
MILLENIUM = 2000
WEEKDAY  = ["PO","UT","STR","STV","PI","SO","NE"];
MONTHS_WITH_30_DAYS = [4, 6, 9, 11]

########################
# Temperature
########################
TMPRTR_REG = 0X11
TMPRTR_REG_NUM = 2
TMPRTR_RESOLUTION = 0.25
TMPRTR_EFFECTIVE_BITS = 10
TMPRTR_NON_EFFECTIVE_BITS = 6
TMPRTR_TWOS_CMPLMNT_MASK = 0b1000000000

# ########################
# # Flags
# ########################
# IS_ON = "is_on"
# SET_LEFT_SCORE = "set_lscore"
# SET_RIGHT_SCORE = "set_rscore"
# SET_HOUR = "set_hour"
# SET_MINUTE = "set_minute"
# SET_BRIGHTNESS = "set_bright"
# BRIGHTNESS_CHANGED = "bright_change"

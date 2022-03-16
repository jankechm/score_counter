# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

from machine import I2C
from matrix.struct import datetime

import matrix.constants as const

class rtc:
    "Adapted from https://github.com/peterhinch/micropython-samples/blob/master/DS3231/ds3231_port.py"

    def __init__(self, i2c: I2C):
        self.i2c = i2c
        self.timebuf = bytearray(const.DATE_TIME_REGS_NUM)

    def _bcd2dec(self, bcd):
        return (((bcd & const.HIGHER_NIBBLE_MASK) >> const.ONE_NIBBLE)
            * const.DEC_BASE + (bcd & const.LOWER_NIBBLE_MASK))

    def _dec2bcd(self, dec):
        tens, ones = divmod(dec, const.DEC_BASE)
        return (tens << const.ONE_NIBBLE) | ones

    def _tobyte(self, num: int):
        return num.to_bytes(1, 'little')
    
    def get_time(self) -> datetime:
        self.i2c.readfrom_mem_into(const.DS3231_I2C_ADDR, 0, self.timebuf)

        seconds = self._bcd2dec(self.timebuf[const.SECONDS_MEM_ADDR])
        minutes = self._bcd2dec(self.timebuf[const.MINUTES_MEM_ADDR])
        hours = self._bcd2dec(self.timebuf[const.HOURS_MEM_ADDR] & 0x3f)
        weekday = self.timebuf[const.WEEKDAY_MEM_ADDR]
        date = self._bcd2dec(self.timebuf[const.DATE_MEM_ADDR])
        month = self._bcd2dec(self.timebuf[const.MONTH_MEM_ADDR] & 0x1f)
        year = self._bcd2dec(self.timebuf[const.YEAR_MEM_ADDR]) + const.MILLENIUM

        return datetime(year, month, date, hours, minutes, seconds, weekday)

    def set_time(self, dt: datetime):
        self.i2c.writeto_mem(const.DS3231_I2C_ADDR, const.SECONDS_MEM_ADDR,
            self._tobyte(self._dec2bcd(dt.seconds)))
        self.i2c.writeto_mem(const.DS3231_I2C_ADDR, const.MINUTES_MEM_ADDR,
            self._tobyte(self._dec2bcd(dt.minutes)))
        self.i2c.writeto_mem(const.DS3231_I2C_ADDR, const.HOURS_MEM_ADDR,
            self._tobyte(self._dec2bcd(dt.hours)))
        self.i2c.writeto_mem(const.DS3231_I2C_ADDR, const.WEEKDAY_MEM_ADDR,
            self._tobyte(self._dec2bcd(dt.weekday)))
        self.i2c.writeto_mem(const.DS3231_I2C_ADDR, const.DATE_MEM_ADDR,
            self._tobyte(self._dec2bcd(dt.date)))
        self.i2c.writeto_mem(const.DS3231_I2C_ADDR, const.MONTH_MEM_ADDR,
            self._tobyte(self._dec2bcd(dt.month)))
        self.i2c.writeto_mem(const.DS3231_I2C_ADDR, const.YEAR_MEM_ADDR,
            self._tobyte(self._dec2bcd(dt.year - const.MILLENIUM)))

    def get_temperature(self) -> float:
        raw_val = self.i2c.readfrom_mem(
            const.DS3231_I2C_ADDR, const.TMPRTR_REG, const.TMPRTR_REG_NUM)

        # first register: upper byte; second register: lower byte
        # omit non-effective bits and align the useful bits in the right order
        aligned_val = (raw_val[0] << const.ONE_BYTE | raw_val[1]) \
            >> const.TMPRTR_NON_EFFECTIVE_BITS

        # decode twos complement
        decoded = -(aligned_val & const.TMPRTR_TWOS_CMPLMNT_MASK) \
            + (aligned_val & ~const.TMPRTR_TWOS_CMPLMNT_MASK)
            
        return decoded * const.TMPRTR_RESOLUTION


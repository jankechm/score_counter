# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

import utime
from machine import I2C
from app.data import Config, Score

import app.constants as const

class EEPROM:
    def __init__(self, i2c: I2C) -> None:
        self.i2c = i2c
        
    def get_cfg(self) -> Config:
        cfg_byte = self.i2c.readfrom_mem(
            const.AT24C32_I2C_ADDR, const.CFG_ADDR, 1, addrsize=16)
        cfg_raw_val = cfg_byte[0]
        
        use_score = bool(cfg_raw_val & const.USE_SCORE_CFG_MASK)
        use_date = bool(cfg_raw_val & const.USE_DATE_CFG_MASK)
        use_time = bool(cfg_raw_val & const.USE_TIME_CFG_MASK)
        use_temperature = bool(cfg_raw_val & const.USE_TEMPERATURE_CFG_MASK)
        scroll = bool(cfg_raw_val & const.SCROLL_CFG_MASK)
        bright_lvl = (cfg_raw_val & const.BRIGHT_LVL_CFG_MASK) \
            >> const.BRIGHT_LVL_BIT_SHIFT

        return Config(
            use_score, use_date, use_time, use_temperature, scroll, bright_lvl)

    def save_cfg(self, cfg: Config):
        val = 0
        if cfg.use_score:
            val |= const.USE_SCORE_CFG_MASK
        if cfg.use_date:
            val |= const.USE_DATE_CFG_MASK
        if cfg.use_time:
            val |= const.USE_TIME_CFG_MASK
        if cfg.use_temperature:
            val |= const.USE_TEMPERATURE_CFG_MASK
        if cfg.scroll:
            val |= const.SCROLL_CFG_MASK
        val |= (cfg.bright_lvl << const.BRIGHT_LVL_BIT_SHIFT) \
            & const.BRIGHT_LVL_CFG_MASK

        self.i2c.writeto_mem(const.AT24C32_I2C_ADDR, const.CFG_ADDR,
            self._tobyte(val), addrsize=16)

        utime.sleep_ms(20) # small pause after each write

    def get_last_score(self) -> Score:
        cfg_byte = self.i2c.readfrom_mem(
            const.AT24C32_I2C_ADDR, const.LAST_SCORE_ADDR, 1, addrsize=16)
        cfg_raw_val = cfg_byte[0]

        left_score = (cfg_raw_val & const.LEFT_SCORE_MASK) \
            >> const.LEFT_SCORE_BIT_SHIFT
        right_score = cfg_raw_val & const.RIGHT_SCORE_MASK

        return Score(left_score, right_score)

    def save_last_score(self, score: Score):
        val = score.right & const.RIGHT_SCORE_MASK
        val |= (score.left << const.LEFT_SCORE_BIT_SHIFT) & const.LEFT_SCORE_MASK

        self.i2c.writeto_mem(const.AT24C32_I2C_ADDR, const.LAST_SCORE_ADDR,
            self._tobyte(val), addrsize=16)

        utime.sleep_ms(20) # small pause after each write

    def _tobyte(self, num: int):
        return num.to_bytes(1, 'little')
# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

import app.font as mx_font
import app.constants as const
from app.data import Score
from app.hw import nv_mem, rtc, display
from app.decorator import singleton

class MxRenderable:
    """
    Abstract class represents information that could be directly rendered
    on the matrix display.
    """

    def render(self, x_shift=0, pre_clear=True, redraw=True):
        pass

class MxNumeric(MxRenderable):
    """
    Represents a numeric information that could be directly rendered
    on the matrix display.
    """

    def __init__(self):
        self._matrix = display

    def _render_2_digit_num(self, num, x_shift=0):
        (tens, ones) = divmod(num, 10)
        ft = mx_font.Medium()

        for digit in [tens, ones]:
            char = ft.get(str(digit))
            char.x_shift(x_shift)
            char.render(self._matrix.fb)

            x_shift += const.COLS_IN_MATRIX

class MxScore(MxNumeric):
    """
    Represents the whole score of both teams that could be rendered 
    on a display.
    """

    ZERO_TENS_DIGIT = 0
    ONE_TENS_DIGIT = 1

    MIN_SCORE = 0
    MAX_SCORE = 99

    class SingleOneDigit(MxRenderable):
        """
        Represents 1 part (left or right) of one-digit-only score (0 - 9).
        """

        X_OFFSET = 4
        X_OFFSET_FOR_1 = 7

        def __init__(self, digit, side):
            self._digit = digit
            self._side = side
            self._matrix = display

        def render(self, x_shift=0):
            offset = x_shift

            if self._digit == 1:
                offset += self.X_OFFSET_FOR_1
            else:
                offset += self.X_OFFSET

            if self._side == const.RIGHT:
                offset += const.RIGHT_SIDE_X_OFFSET

            font = mx_font.BigDigit()

            renderable = font.get(self._digit)
            renderable.x_shift(offset)
            renderable.render(self._matrix.fb)

    class SingleTwoDigit(MxRenderable):
        """
        Represents 1 part (left or right) of two-digit score,
        where digit 1 is on the place of tens (score 10 - 19).
        """

        TENS_X_OFFSET = 2
        ONES_X_OFFSET = 6
        ONES_X_OFFSET_FOR_1 = 12

        def __init__(self, tens, ones, side):
            self._tens = tens
            self._ones = ones
            self._side = side
            self._matrix = display

        def render(self, x_shift=0):
            tens_offset = x_shift
            ones_offset = x_shift

            tens_offset += self.TENS_X_OFFSET

            if self._ones == 1:
                ones_offset += self.ONES_X_OFFSET_FOR_1
            else:
                ones_offset += self.ONES_X_OFFSET

            if self._side == const.RIGHT:
                tens_offset += const.RIGHT_SIDE_X_OFFSET
                ones_offset += const.RIGHT_SIDE_X_OFFSET

            font = mx_font.BigDigit()

            renderable_ones = font.get(self._tens)
            renderable_ones.x_shift(tens_offset)
            renderable_ones.render(self._matrix.fb)

            renderable_ones = font.get(self._ones)
            renderable_ones.x_shift(ones_offset)
            renderable_ones.render(self._matrix.fb)

    class SingleHigherTwoDigit(MxNumeric):
        """
        Represents 1 part (left or right) of two-digit score,
        where digit higher than 1 is on the place of tens (score 20 - 99).
        The main difference is in the used font, which is smaller
        than the font used in classes represting score lower than 20.
        The reason for that is that the digits of tens and ones would converge
        on the display if a bigger font would be used.
        """

        RIGHT_SCORE_X_SHIFT = 18

        def __init__(self, single_score, side):
            super().__init__()

            self._single_score = single_score
            self._side = side

        def render(self, x_shift=0):
            if self._side == const.RIGHT:
                x_shift += self.RIGHT_SCORE_X_SHIFT

            self._render_2_digit_num(self._single_score, x_shift)
    
    
    def __init__(self) -> None:
        super().__init__()

        self._nv_mem = nv_mem
        self._last_changed = const.LEFT_AND_RIGHT

        self.load()

        self._prev_score = Score(self._score.left, self._score.right)

    def revert(self):
        if self._last_changed == const.LEFT:
            self._score.left = self._prev_score.left
        elif self._last_changed == const.RIGHT:
            self._score.right = self._prev_score.right
        else:
            self._score.left = self._prev_score.left
            self._score.right = self._prev_score.right

        self.save()

    def reset(self):
        self._last_changed = const.LEFT_AND_RIGHT

        self._score.left = 0
        self._score.right = 0

        self.save()

    def set_score(self, l_val, r_val):
        self._last_changed = const.LEFT_AND_RIGHT

        self.set_left(l_val)
        self.set_right(r_val)

    def set_left(self, val):
        self._last_changed = const.LEFT

        if val > self.MAX_SCORE:
            self._score.left = self.MAX_SCORE
        elif val < self.MIN_SCORE:
            self._score.left = self.MIN_SCORE
        else:
            self._score.left = val

    def set_right(self, val):
        self._last_changed = const.RIGHT

        if val > self.MAX_SCORE:
            self._score.right = self.MAX_SCORE
        elif val < self.MIN_SCORE:
            self._score.right = self.MIN_SCORE
        else:
            self._score.right = val

    def incr_left(self):
        """
        Update previous score, increment current left score
        and save current score to the non-volatile memory.
        """

        self.set_left(self._score.left + 1)

    def decr_left(self):
        """
        Update previous score, decrement current left score
        and save current score to the non-volatile memory.
        """

        self.set_left(self._score.left - 1)
    
    def incr_right(self):
        """
        Update previous score, increment current right score
        and save current score to the non-volatile memory.
        """

        self.set_right(self._score.right + 1)

    def decr_right(self):
        """
        Update previous score, decrement current right score
        and save current score to the non-volatile memory.
        """

        self.set_right(self._score.right - 1)

    def get_last_changed_side(self):
        return self._last_changed

    def load(self):
        """
        Fetch the score from the non-volatile memory.
        """

        self._score = self._nv_mem.get_last_score()

    def save(self):
        """
        Confirm score and save it to the non-volatile memory.
        """

        self._prev_score = self._nv_mem.get_last_score()
        self._nv_mem.save_last_score(self._score)

    def render(self, x_shift=0, pre_clear=True, redraw=True):
        if pre_clear:
            self._matrix.fill(0)

        (l_tens, l_ones) = divmod(self._score.left, 10)
        (r_tens, r_ones) = divmod(self._score.right, 10)

        if l_tens > self.ONE_TENS_DIGIT or r_tens > self.ONE_TENS_DIGIT:
            l_score = self.SingleHigherTwoDigit(self._score.left, const.LEFT)
            r_score = self.SingleHigherTwoDigit(self._score.right, const.RIGHT)
        else:
            if l_tens == self.ZERO_TENS_DIGIT:
                l_score = self.SingleOneDigit(l_ones, const.LEFT)
            else:
                l_score = self.SingleTwoDigit(l_tens, l_ones, const.LEFT)

            if r_tens == self.ZERO_TENS_DIGIT:
                r_score = self.SingleOneDigit(r_ones, const.RIGHT)
            else:
                r_score = self.SingleTwoDigit(r_tens, r_ones, const.RIGHT)

        l_score.render(x_shift)
        self._render_score_delimiter(x_shift)
        r_score.render(x_shift)

        if redraw:
            self._matrix.redraw_twice()

    def _render_score_delimiter(self, x_shift):
        self._matrix.hline(15 + x_shift, 7, 2, 1)
        self._matrix.hline(15 + x_shift, 8, 2, 1)

@singleton
class MxDate(MxNumeric):
    DAY_X_SHIFT = 18
    DAY_ORDINAL_DOT_X_SHIFT = 18

    MAX_MONTH = 12
    MIN_MONTH = 1
    MAX_DAY = 31
    MAX_DAY_30 = 30
    MIN_DAY = 1
    MIN_YEAR = 2000
    MAX_YEAR = 2099

    MONTHS_WITH_30_DAYS = [4, 6, 9, 11]

    def __init__(self) -> None:
        super().__init__()

        self._rtc = rtc
        self.pull()

    def set_date(self, month, day, year=None):
        self.set_day(day)
        self.set_month(month)

        self.validate_max_days()

        if year is not None:
            self.set_year(year)

    def set_month(self, month):
        if month > self.MAX_MONTH:
            self._month = self.MAX_MONTH
        elif month < self.MIN_MONTH:
            self._month = self.MIN_MONTH
        else:
            self._month = month

    def set_day(self, day):
        if day > self.MAX_DAY:
            self._day = self.MAX_DAY
        elif day < self.MIN_DAY:
            self._day = self.MIN_DAY
        else:
            self._day = day

    def set_year(self, year):
        if year > self.MAX_YEAR:
            self._year = self.MAX_YEAR
        elif year < self.MIN_YEAR:
            self._year = self.MIN_YEAR
        else:
            self._year = year

    def validate_max_days(self):
        if self._month in self.MONTHS_WITH_30_DAYS and self._day >= self.MAX_DAY:
            self._day = self.MAX_DAY_30

    def incr_month(self):
        """
        Cyclic month increment.
        """

        if self._month == self.MAX_MONTH:
            self._month = self.MIN_MONTH
        else:
            self._month += 1
    
    def decr_month(self):
        """
        Cyclic month decrement.
        """

        if self._month == self.MIN_MONTH:
            self._month = self.MAX_MONTH
        else:
            self._month -= 1

    def incr_day(self):
        """
        Cyclic day increment.
        """
        
        if self._day == self.MAX_DAY:
            self._day = self.MIN_DAY
        else:
            self._day += 1

    def decr_day(self):
        """
        Cyclic day decrement.
        """

        if self._day == self.MIN_DAY:
            self._day = self.MAX_DAY
        else:
            self._day -= 1

    def incr_year(self):
        """
        Cyclic year increment.
        """

        if self._year == self.MAX_YEAR:
            self._year = self.MIN_YEAR
        else:
            self._year += 1

    def decr_year(self):
        """
        Cyclic year decrement.
        """

        if self._year == self.MIN_YEAR:
            self._year = self.MAX_YEAR
        else:
            self._year -= 1

    def pull(self):
        """
        Fetch the date from the Real Time Clock module.
        """

        datetime = self._rtc.get_time()

        self._day = datetime.date
        self._month = datetime.month
        self._year = datetime.year

    def push(self):
        """
        Fetch the date from the Real Time Clock module,
        set the month & day & year and push it back to the RTC.
        """

        datetime = self._rtc.get_time()

        datetime.month = self._month
        datetime.date = self._day
        datetime.year = self._year

        self._rtc.set_time(datetime)

    def render_setting(self):
        """
        Render the day and month on one line and year on the second line.
        This is intended for rendering just during date setting.
        """

        self._matrix.fill(0)

        self._matrix.text("{:02d}{:02d}".format(self._day, self._month), 0, 0)
        self._matrix.text(str(self._year), 0, 8)

        self._render_date_setting_ordinal_dots(0)

        self._matrix.redraw_twice()

    def _render_date_setting_ordinal_dots(self, x_shift):
        self._matrix.pixel(15 + x_shift, 7, 1)
        self._matrix.pixel(31 + x_shift, 7, 1)

    def render(self, x_shift=0, pre_clear=True, redraw=True):
        """
        Render the day and month with their ordinal dots. No year rendering.
        This is intended for rendering during basic operation mode.
        """

        self.pull()

        if pre_clear:
            self._matrix.fill(0)

        self._render_2_digit_num(self._day, x_shift)
        self._render_ordinal_dot(x_shift)
        self._render_2_digit_num(self._month, x_shift + self.DAY_X_SHIFT)
        self._render_ordinal_dot(x_shift + self.DAY_ORDINAL_DOT_X_SHIFT)

        if redraw:
            self._matrix.redraw_twice()

    def _render_ordinal_dot(self, x_shift=0):
        self._matrix.hline(15 + x_shift, 13, 2, 1)
        self._matrix.hline(15 + x_shift, 14, 2, 1)

@singleton
class MxTime(MxNumeric):
    MINUTES_X_SHIFT = 18
    MAX_HOURS = 23
    MIN_HOURS = 0
    MAX_MINUTES = 59
    MIN_MINUTES = 0

    def __init__(self) -> None:
        super().__init__()
        
        self._rtc = rtc
        self.pull()

    def set_time(self, hours, minutes):
        self.set_hours(hours)
        self.set_minutes(minutes)

    def set_hours(self, hours):
        if hours > self.MAX_HOURS:
            self._hours = self.MAX_HOURS
        elif hours < self.MIN_HOURS:
            self._hours = self.MIN_HOURS
        else:
            self._hours = hours

    def set_minutes(self, minutes):
        if minutes > self.MAX_MINUTES:
            self._minutes = self.MAX_MINUTES
        elif minutes < self.MIN_MINUTES:
            self._minutes = self.MIN_MINUTES
        else:
            self._minutes = minutes
    
    def incr_hour(self):
        """
        Cyclic hour increment.
        """

        if self._hours == self.MAX_HOURS:
            self._hours = self.MIN_HOURS
        else:
            self._hours += 1
    
    def decr_hour(self):
        """
        Cyclic hour decrement.
        """

        if self._hours == self.MIN_HOURS:
            self._hours = self.MAX_HOURS
        else:
            self._hours -= 1

    def incr_minute(self):
        """
        Cyclic minute increment.
        """

        if self._minutes == self.MAX_MINUTES:
            self._minutes = self.MIN_MINUTES
        else:
            self._minutes += 1

    def decr_minute(self):
        """
        Cyclic minute decrement.
        """

        if self._minutes == self.MIN_MINUTES:
            self._minutes = self.MAX_MINUTES
        else:
            self._minutes -= 1

    def pull(self):
        """
        Fetch the time from the Real Time Clock module.
        """

        datetime = self._rtc.get_time()

        self._hours = datetime.hours
        self._minutes = datetime.minutes

    def push(self):
        """
        Fetch the time from the Real Time Clock module,
        set the hours, minutes & seconds and push it back to the RTC.
        """

        datetime = self._rtc.get_time()

        datetime.hours = self._hours
        datetime.minutes = self._minutes
        datetime.seconds = 0

        self._rtc.set_time(datetime)

    def render_setting(self, x_shift=0, pre_clear=True, redraw=True):
        """
        This is intended for rendering during time setting.
        """

        if pre_clear:
            self._matrix.fill(0)

        self._render_2_digit_num(self._hours, x_shift)
        self._render_time_delimiter(x_shift)
        self._render_2_digit_num(self._minutes, x_shift + self.MINUTES_X_SHIFT)

        if redraw:
            self._matrix.redraw_twice()

    def render(self, x_shift=0, pre_clear=True, redraw=True):
        """
        This method pulls the actual time from the RTC module before rendering.
        """

        self.pull()

        self.render_setting(x_shift, pre_clear, redraw)

    def _render_time_delimiter(self, x_shift=0):
        self._matrix.hline(15 + x_shift, 4, 2, 1)
        self._matrix.hline(15 + x_shift, 5, 2, 1)
        self._matrix.hline(15 + x_shift, 10, 2, 1)
        self._matrix.hline(15 + x_shift, 11, 2, 1)

@singleton
class MxTemperature(MxNumeric):
    def __init__(self) -> None:
        super().__init__()
        
        self._rtc = rtc
        self.pull()

    def pull(self):
        """
        Fetch the temperature from the Real Time Clock module's sensor.
        """

        self._temperature = self._rtc.get_temperature()

    def render(self, x_shift=0, pre_clear=True, redraw=True):
        self.pull()

        if pre_clear:
            self._matrix.fill(0)
        
        self._render_2_digit_num(int(self._temperature), x_shift)

        font = mx_font.Medium()

        degree = font.get("°")
        c_char = font.get("C")

        degree.x_shift(const.COLS_IN_MATRIX * 2 + x_shift)
        c_char.x_shift(const.COLS_IN_MATRIX * 3 + x_shift)
        
        degree.render(self._matrix.fb)
        c_char.render(self._matrix.fb)

        if redraw:
            self._matrix.redraw_twice()

class MxBrightness(MxRenderable):
    MAX_LVL = 3
    MIN_LVL = 0

    def __init__(self):
        self._nv_mem = nv_mem
        self._matrix = display
        self.load()

    def set_lvl(self, lvl: int):
        if lvl > MxBrightness.MAX_LVL:
            lvl = MxBrightness.MAX_LVL
        elif lvl < MxBrightness.MIN_LVL:
            lvl = MxBrightness.MIN_LVL
        else:
            self._level = lvl

    def get_lvl(self):
        return self._level
    
    def incr(self):
        self.set_lvl(self._level + 1)

    def decr(self):
        self.set_lvl(self._level - 1)

    def save(self):
        config = self._nv_mem.get_cfg()
        config.bright_lvl = self._level
        self._nv_mem.save_cfg(config)
    
    def load(self):
        self.set_lvl(self._nv_mem.get_cfg().bright_lvl)

    def mx_set(self):
        self._matrix.set_brightness(self._level)

    def render(self, x_shift=0, pre_clear=True, redraw=True):
        if pre_clear:
            self._matrix.fill(0)

        font = mx_font.Medium()

        j_char = font.get("J")
        a_char = font.get("A")
        s_char = font.get("S")
        lvl_char = font.get(str(self._level))

        a_char.x_shift(const.COLS_IN_MATRIX + x_shift)
        s_char.x_shift(const.COLS_IN_MATRIX * 2 + x_shift)
        lvl_char.x_shift(const.COLS_IN_MATRIX * 3 + x_shift)

        j_char.render(self._matrix.fb)
        a_char.render(self._matrix.fb)
        s_char.render(self._matrix.fb)
        lvl_char.render(self._matrix.fb)

        if redraw:
            self._matrix.redraw_twice()

class MxUsageCfg(MxRenderable):
    def __init__(self) -> None:
        self._nv_mem = nv_mem
        self._matrix = display

        self._text = ""
        self.use_it = False

        self.load()

    def load(self):
        pass

    def save(self):
        pass

    def get_txt_len(self):
        return len(self._text)

    def render(self, x_shift=0, pre_clear=True, redraw=True):
        if pre_clear:
            self._matrix.fill(0)

        if self.use_it:
            value = "On"
        else:
            value = "Off"

        self._matrix.text(self._text, 0 + x_shift, 0)
        self._matrix.text(value, 0, 8)

        if redraw:
            self._matrix.redraw_twice()

@singleton
class MxUseScoreCfg(MxUsageCfg):
    def __init__(self) -> None:
        super().__init__()

        self._text = "skore"

    def load(self):
        self.use_it = self._nv_mem.get_cfg().use_score

    def save(self):
        config = self._nv_mem.get_cfg()
        config.use_score = self.use_it
        self._nv_mem.save_cfg(config)

@singleton
class MxUseDateCfg(MxUsageCfg):
    def __init__(self) -> None:
        super().__init__()

        self._text = "datum"

    def load(self):
        self.use_it = self._nv_mem.get_cfg().use_date

    def save(self):
        config = self._nv_mem.get_cfg()
        config.use_date = self.use_it
        self._nv_mem.save_cfg(config)

@singleton
class MxUseTimeCfg(MxUsageCfg):
    def __init__(self) -> None:
        super().__init__()

        self._text = "cas"

    def load(self):
        self.use_it = self._nv_mem.get_cfg().use_time

    def save(self):
        config = self._nv_mem.get_cfg()
        config.use_time = self.use_it
        self._nv_mem.save_cfg(config)

@singleton
class MxUseTemperatureCfg(MxUsageCfg):
    def __init__(self) -> None:
        super().__init__()

        self._text = "teplota"

    def load(self):
        self.use_it = self._nv_mem.get_cfg().use_temperature

    def save(self):
        config = self._nv_mem.get_cfg()
        config.use_temperature = self.use_it
        self._nv_mem.save_cfg(config)

@singleton
class MxUseScrollingCfg(MxUsageCfg):
    def __init__(self) -> None:
        super().__init__()

        self._text = "scroll"

    def load(self):
        self.use_it = self._nv_mem.get_cfg().scroll

    def save(self):
        config = self._nv_mem.get_cfg()
        config.scroll = self.use_it
        self._nv_mem.save_cfg(config)

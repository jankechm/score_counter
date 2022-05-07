# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

import uasyncio as asyncio
import app.constants as const
from app.adt import CircularList
from app.hw import nv_mem, display
from app.mx_data import MxRenderable, MxDate, MxTime, MxTemperature, MxUsageCfg, MxUseScoreCfg, MxUseDateCfg, MxUseTimeCfg, MxUseTemperatureCfg, MxUseScrollingCfg

SPACE = 8

FIVE_MILLIS = 5
TEN_MILLIS = 10
TWENTY_MILLIS = 20
THIRTY_MILLIS = 30

NO_VIEW = 0

class BasicViewer:
    ONE_INFO_LEN = 32
    TWO_INFO = 2
    
    SCROLL_MODE = 1
    ALTERNATE_MODE = 2

    def __init__(self):
        self._nv_mem = nv_mem
        self._matrix = display

        self.score = None
        self._to_render = []

        self.load()

    def load(self):
        self._to_render = []
        config = self._nv_mem.get_cfg()

        if config.use_score and self.score is not None:
            self._to_render.append(self.score)
        if config.use_date:
            self._to_render.append(MxDate())
        if config.use_time:
            self._to_render.append(MxTime())
        if config.use_temperature:
            self._to_render.append(MxTemperature())
        
        if config.scroll:
            self._view_mode = self.SCROLL_MODE
        else:
            self._view_mode = self.ALTERNATE_MODE

    def disable(self):
        self._view_mode = NO_VIEW

    async def view_info(self):
        self.load()

        if self._view_mode == self.SCROLL_MODE:
            await self._scroll()
        else:
            await self._alternate()

    async def _alternate(self):
        """
        This couroutine can alternate multiple text information on the display
        based on loaded configuration from the memory.
        It loops through a circular list of renderable info, so unless 
        :func:`disable` is called, it never ends.
        """

        if self._to_render:
            circular_to_render = CircularList(self._to_render)

            while self._view_mode == self.ALTERNATE_MODE:
                circular_to_render.next().render()
                await asyncio.sleep_ms(2000)

    async def _scroll(self):
        """
        This couroutine can scroll multiple text information on the display
        based on loaded configuration from the memory.
        It loops through a circular list of renderable info, so unless 
        :func:`disable` is called, it never ends.
        """

        if self._to_render:
            circular_to_render = CircularList(self._to_render)

            obj1 = circular_to_render.next()
            await self._scroll_basic_info_1(obj1)

            while self._view_mode == self.SCROLL_MODE:
                obj2 = circular_to_render.next()
                await self._scroll_basic_info_2(obj1, obj2)

                obj1 = obj2

    async def _scroll_basic_info_1(self, obj: MxRenderable):
        """
        This couroutine is intended to be called once at the beginning
        of text scrolling, when there was no previous text displayed.
        Only one text info is displayed.
        """

        for x_shift in range(self.ONE_INFO_LEN, 0, -1):
            if self._view_mode != self.SCROLL_MODE:
                break
            
            obj.render(x_shift)

            await asyncio.sleep_ms(TEN_MILLIS)

    async def _scroll_basic_info_2(self, obj1: MxRenderable, obj2: MxRenderable):
        """
        This couroutine is intended to be called in a cycle, 
        if the :func:`_scroll_basic_info_1` was already called right before.
        It starts where the :func:`_scroll_basic_info_1` ended and
        ends with the second text info displayed.
        """

        for x_shift in range(0, -(SPACE + self.ONE_INFO_LEN), -1):
            if self._view_mode != self.SCROLL_MODE:
                break
            
            self._matrix.fill(0)

            obj1.render(x_shift, False, False)
            obj2.render(x_shift + SPACE + self.ONE_INFO_LEN, False, False)

            self._matrix.redraw_twice()

            await asyncio.sleep_ms(FIVE_MILLIS)


class SettingsViewer:
    CFG_INFO_INIT_CHAR_SHIFT = 1

    USE_SCORE_CFG_VIEW = 2
    USE_DATE_CFG_VIEW = 3
    USE_TIME_CFG_VIEW = 4
    USE_TEMPERATURE_CFG_VIEW = 5
    USE_SCROLLING_CFG_VIEW = 6

    def __init__(self):
        self._matrix = display

    def disable(self):
        self._view_mode = NO_VIEW

    async def scroll_score_cfg(self):
        await self._scroll_cfg(MxUseScoreCfg(), self.USE_SCORE_CFG_VIEW)

    async def scroll_date_cfg(self):
        await self._scroll_cfg(MxUseDateCfg(), self.USE_DATE_CFG_VIEW)

    async def scroll_time_cfg(self):
        await self._scroll_cfg(MxUseTimeCfg(), self.USE_TIME_CFG_VIEW)

    async def scroll_temperature_cfg(self):
        await self._scroll_cfg(MxUseTemperatureCfg(), self.USE_TEMPERATURE_CFG_VIEW)

    async def scroll_scrolling_cfg(self):
        await self._scroll_cfg(MxUseScrollingCfg(), self.USE_SCROLLING_CFG_VIEW)

    async def _scroll_cfg(self, obj: MxUsageCfg, mode):
        self._view_mode = mode

        await self._scroll_cfg_1(obj, mode)

        while self._view_mode == mode:
            await self._scroll_cfg_2(obj, mode)
    
    async def _scroll_cfg_1(self, obj: MxUsageCfg, mode):
        """
        This couroutine is intended to be called once at the beginning
        of text scrolling, when there was no previous text displayed.
        """

        start = self.CFG_INFO_INIT_CHAR_SHIFT * const.COLS_IN_MATRIX
        stop = -((obj.get_txt_len() - const.MATRIXES_IN_ROW 
            + self.CFG_INFO_INIT_CHAR_SHIFT) * const.COLS_IN_MATRIX)

        for x_shift in range(start, stop, -1):
            if self._view_mode != mode:
                break
            
            obj.render(x_shift)

            await asyncio.sleep_ms(TWENTY_MILLIS)

    async def _scroll_cfg_2(self, obj: MxUsageCfg, mode):
        """
        This couroutine is intended to be called in a cycle, 
        if the :func:`_scroll_cfg_1` was already called right before.
        It starts where the :func:`_scroll_cfg_1` ended and
        ends with the text at the same position.
        """

        text_len = obj.get_txt_len()
        start = -((text_len - const.MATRIXES_IN_ROW 
            + self.CFG_INFO_INIT_CHAR_SHIFT) * const.COLS_IN_MATRIX)
        stop = start - (SPACE + text_len * const.COLS_IN_MATRIX)

        for x_shift in range(start, stop, -1):
            if self._view_mode != mode:
                break
            
            self._matrix.fill(0)

            obj.render(x_shift + SPACE + text_len * const.COLS_IN_MATRIX,
                False, False)
            obj.render(x_shift, False, False)

            self._matrix.redraw_twice()

            await asyncio.sleep_ms(TWENTY_MILLIS)

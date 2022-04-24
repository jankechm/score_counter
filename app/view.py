# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

import uasyncio as asyncio
import app.constants as const
from app.hw import rtc, nv_mem, display
from app.mx_data import MxRenderable, MxScore, MxDate, MxTime

class Viewer:
    ONE_INFO_LEN = 32
    TWO_INFO = 2
    SPACE = 8
    MS_BETWEEN_TRANSITION = 30
    MS_BETWEEN_TRANSITION_2 = 20

    def __init__(self, score: MxScore):
        self._rtc = rtc
        self._nv_mem = nv_mem
        self._matrix = display

        self._score = score
        self._to_render = []

        self.load()

        self._should_run = True

    def load(self):
        config = self._nv_mem.get_cfg()

        if True:
            self._to_render.append(self._score)
        if config.use_date:
            self._to_render.append(MxDate())
        if config.use_time:
            self._to_render.append(MxTime())

    def enable(self):
        self._should_run = True
    
    def disable(self):
        self._should_run = False

    async def scroll(self):
        if self._to_render:
            circular_to_render = CircularList(self._to_render)

            obj1 = circular_to_render.next()
            await self.scroll_1(obj1)

            while self._should_run:
                obj2 = circular_to_render.next()
                await self.scroll_2(obj1, obj2)

                obj1 = obj2

    async def scroll_1(self, obj: MxRenderable):
        for x_shift in range(self.ONE_INFO_LEN, 0, -1):
            if not self._should_run:
                break
            
            obj.render(x_shift)

            await asyncio.sleep_ms(self.MS_BETWEEN_TRANSITION)

    async def scroll_2(self, obj1: MxRenderable, obj2: MxRenderable):
        for x_shift in range(0, -(self.SPACE + self.ONE_INFO_LEN), -1):
            if not self._should_run:
                break
            
            self._matrix.fill(0)

            obj1.render(x_shift, False, False)
            obj2.render(x_shift + self.SPACE + self.ONE_INFO_LEN, False, False)

            self._matrix.redraw_twice()

            await asyncio.sleep_ms(self.MS_BETWEEN_TRANSITION_2)

class CircularList:
    def __init__(self, lst) -> None:
        if not lst:
            raise ValueError
        self._lst = lst
        self._index = None
        self._max_index = len(lst) - 1

    def next(self):
        if self._index is None or self._index == self._max_index:
            self._index = 0
        else:
            self._index += 1        
        return self._lst[self._index]

    def prev(self):
        if self._index is None or self._index == 0:
            self._index = self._max_index
        else:
            self._index -= 1
        return self._lst[self._index]
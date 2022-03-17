# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

class Score:
    def __init__(self, left: int, right: int) -> None:
        self.left = left
        self.right = right

class Datetime:
    def __init__(self, year, month, date, hours, minutes, seconds, weekday):
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.weekday = weekday
        self.date = date
        self.month = month
        self.year = year

class Config:
    def __init__(self, scroll: bool, use_time: bool, use_date: bool,
        use_temperature: bool, bright_lvl: int) -> None:
        self.scroll = scroll
        self.use_time = use_time
        self.use_date = use_date
        self.use_temperature = use_temperature
        self.bright_lvl = bright_lvl
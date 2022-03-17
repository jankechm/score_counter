# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

from machine import Pin, SPI, I2C
from lib.ir_rx.nec import NEC_8  # NEC remote, 8 bit addresses
from app.mx import Matrix
from app.clock import RTC
from mem import EEPROM
from app.data import Datetime

import uasyncio as asyncio
import app.constants as const

import micropython
import utime
import gc

class App:
	def __init__(self):
		"""
		Main application. 
		Evaluates user inputs from remote control and performs appropriate
		actions on matrix display.
		It uses asynchronous tasks execution (cooperative multitasking)
		to pretend parallelism.
		"""

		self.set_left_score = False
		self.set_right_score = False
		self.set_day = False
		self.set_month = False
		self.set_year = False
		self.set_hour = False
		self.set_minute = False
		self.set_brightness = False
		self.brightness_changed = False
		self.basic_mode = True
		self.is_on = True
		
		self.left_score = 0
		self.right_score = 0
		self.dt = Datetime(2022, 1, 1, 0, 0, 0, 7)
		self.brightness = 1
		self.last_button = 0x00

	def button_handler(self, button, addr, ctrl):
		if button == const.BUTTON_0:
			self.handle_btn_0()
		elif button == const.BUTTON_1:
			self.handle_btn_1()
		elif button == const.BUTTON_9:
			self.handle_btn_9()
		elif button == const.BUTTON_LEFT:
			self.handle_btn_left()
		elif button == const.BUTTON_RIGHT:
			self.handle_btn_right()
		elif button == const.BUTTON_UP:
			self.handle_btn_up()
		elif button == const.BUTTON_DOWN:
			self.handle_btn_down()
		elif button == const.BUTTON_STAR:
			self.handle_btn_star()
		elif button == const.BUTTON_HASH:
			self.handle_btn_hash()
		elif button == const.BUTTON_OK:
			self.handle_btn_ok()
		# Only allow hold of BUTTON_UP or BUTTON_DOWN as repeated push
		elif button == NEC_8.REPEAT and\
		self.last_button in [const.BUTTON_UP, const.BUTTON_DOWN]:
			# Recursive call with concrete button
			self.button_handler(self.last_button, addr, ctrl)

		# Set last pushed button if not repeat code button
		if button != NEC_8.REPEAT:
			self.last_button = button

	def handle_btn_0(self):
		if self.set_left_score:
			self.left_score = 0
			self.display.show_score(self.left_score, self.right_score)
			# print("Left score set to 0")
		elif self.set_right_score:
			self.right_score = 0
			self.display.show_score(self.left_score, self.right_score)
			# print("Right score set to 0")
		elif self.set_hour:
			self.dt.hours = 0
			self.display.show_time(self.dt.hours, self.dt.minutes)
			# print("Hour reset set to 0")
		elif self.set_minute:
			self.dt.minutes = 0
			self.display.show_time(self.dt.hours, self.dt.minutes)
			# print("Minute set to 0")
		elif self.set_brightness:
			self.brightness = 0
			self.brightness_changed = True
			# print("Brightness set to 0")

	def handle_btn_1(self):
		if self.basic_mode:
			self.set_brightness = True
			self.brightness_changed = True
			self.basic_mode = False
			print("Setting brightness...")

	def handle_btn_9(self):
		if self.basic_mode:
			self.set_day = True
			self.basic_mode = False
			self.dt = self.clock.get_time()
			self.display.show_date_setting(
				self.dt.date, self.dt.month, self.dt.year)

	def handle_btn_left(self):
		if self.basic_mode:
			self.set_left_score = True
			self.basic_mode = False
			self.display.show_score(self.left_score, self.right_score)
			print("Setting left score...")

	def handle_btn_right(self):
		if self.basic_mode:
			self.set_right_score = True
			self.basic_mode = False
			self.display.show_score(self.left_score, self.right_score)
			print("Setting right score...")

	def handle_btn_up(self):
		if self.set_left_score:
			t_curr = utime.ticks_ms()
			t_diff = utime.ticks_diff(t_curr, self.ticks)
			# Avoid two increments in very short time
			if t_diff > 200 or t_diff < 0:
			# if True:
				self.left_score += 1
				self.ticks = t_curr
				self.display.show_score(self.left_score, self.right_score)
				# print("Left score incremented to: {}".format(self.left_score))
		elif self.set_right_score:
			self.right_score += 1
			self.display.show_score(self.left_score, self.right_score)
			# print("Right score incremented to: {}".format(self.right_score))
		elif self.set_day:
			if self.dt.date < 31:
				self.dt.date += 1
			else:
				self.dt.date = 1
			self.display.show_date_setting(self.dt.date, self.dt.month, self.dt.year)
		elif self.set_month:
			if self.dt.month < 12:
				self.dt.month += 1
			else:
				self.dt.month = 1
			self.display.show_date_setting(self.dt.date, self.dt.month, self.dt.year)
		elif self.set_year:
			if self.dt.year < 2099:
				self.dt.year += 1
			else:
				self.dt.year = 2000
			self.display.show_date_setting(self.dt.date, self.dt.month, self.dt.year)
		elif self.set_hour:
			if self.dt.hours < 23:
				self.dt.hours += 1
			else:
				self.dt.hours = 0
			# print("Hour set to: {}".format(self.dt.hours))
			self.display.show_time(self.dt.hours, self.dt.minutes)
		elif self.set_minute:
			if self.dt.minutes < 59:
				self.dt.minutes += 1
			else:
				self.dt.minutes = 0
			# print("Minute set to: {}".format(self.dt.minutes))
			self.display.show_time(self.dt.hours, self.dt.minutes)
		elif self.set_brightness:
			if self.brightness < 3:
				self.brightness += 1
			else:
				self.brightness = 0
			self.brightness_changed = True

	def handle_btn_down(self):
		if self.set_left_score:
			if self.left_score > 0:
				self.left_score -= 1
				# print("Left score decremented to: {}".format(self.left_score))
			self.display.show_score(self.left_score, self.right_score)
		elif self.set_right_score:
			if self.right_score > 0:
				self.right_score -= 1
				# print("Right score decremented to: {}".format(self.right_score))
			self.display.show_score(self.left_score, self.right_score)
		elif self.set_day:
			if self.dt.date > 1:
				self.dt.date -= 1
			else:
				self.dt.date = 31
			self.display.show_date_setting(self.dt.date, self.dt.month, self.dt.year)
		elif self.set_month:
			if self.dt.month > 1:
				self.dt.month -= 1
			else:
				self.dt.month = 12
			self.display.show_date_setting(self.dt.date, self.dt.month, self.dt.year)
		elif self.set_year:
			if self.dt.year > 2000:
				self.dt.year -= 1
			else:
				self.dt.year = 2099
			self.display.show_date_setting(self.dt.date, self.dt.month, self.dt.year)
		elif self.set_hour:
			if self.dt.hours > 0:
				self.dt.hours -= 1
			else:
				self.dt.hours = 23
			# print("Hour set to: {}".format(self.dt.hours))
			self.display.show_time(self.dt.hours, self.dt.minutes)
		elif self.set_minute:
			if self.dt.minutes > 0:
				self.dt.minutes -= 1
			else:
				self.dt.minutes = 59
			# print("Minute set to: {}".format(self.dt.minutes))
			self.display.show_time(self.dt.hours, self.dt.minutes)
		elif self.set_brightness:
			if self.brightness > 0:
				self.brightness -= 1
			else:
				self.brightness = 3
			self.brightness_changed = True

	def handle_btn_star(self):
		if self.is_on:
			print("Off")
			self.display.turn_off()
			self.is_on = False
		else:
			print("On")
			self.display.turn_on()
			self.is_on = True

	def handle_btn_hash(self):
		print("Resetting display...")
		self.display.init_display(self.config.bright_lvl)

	def handle_btn_ok(self):
		if self.set_left_score:
			self.set_left_score = False
			self.basic_mode = True
			print("Left score set!")
		elif self.set_right_score:
			self.set_right_score = False
			self.basic_mode = True
			print("Right score set!")
		elif self.set_day:
			self.set_day = False
			self.set_month = True
		elif self.set_month:
			self.set_month = False
			self.set_year = True
			# validate max days in the month
			if self.dt.month in const.MONTHS_WITH_30_DAYS and self.dt.date > 30:
				self.dt.date = 30
		elif self.set_year:
			self.set_year = False
			self.set_hour = True
		elif self.set_hour:
			self.set_hour = False
			self.set_minute = True
			print("Hour set!")
		elif self.set_minute:
			self.clock.set_time(self.dt)
			self.set_minute = False
			self.basic_mode = True
			print("Minute set!")
		elif self.set_brightness:
			self.set_brightness = False
			self.basic_mode = True

	async def led_blink(self):
		led_onboard = Pin(25, Pin.OUT)

		while True:
			led_onboard.toggle()
			await asyncio.sleep_ms(500)

	async def mem_monitor(self):
		while True:
			print("Free memory: {:.2f} KB".format(gc.mem_free() / 1024))
			await asyncio.sleep_ms(3000)

	async def basic_operation(self):
		while True:
			if self.basic_mode:
				# Ensure no interrupts when reading/showing score
				self.receiver.disable_irq()
				self.display.show_score(self.left_score, self.right_score)
				self.receiver.enable_irq()
				await asyncio.sleep_ms(3000)

				# Need to check again
				if self.basic_mode:
					await self.scroll_secondary_info()
					# self.dt = self.clock.get_time()
					# self.display.show_time(self.dt.hours, self.dt.minutes)
					# await asyncio.sleep_ms(2000)
			# pass execution to other tasks
			await asyncio.sleep_ms(0)

	async def scroll_secondary_info(self):
		info_len = 12 * const.COLS_IN_MATRIX + 8
		info_len = 5 * const.COLS_IN_MATRIX

		for x_shift in range(32, -info_len, -1):
			if not self.basic_mode:
				break
			
			self.dt = self.clock.get_time()
			self.dt.date = -1
			temperature = self.clock.get_temperature()
			temperature = -1

			self.display.show_variable_info(x_shift, self.dt, int(temperature))

			await asyncio.sleep_ms(30)
			# await asyncio.sleep_ms(60)

	async def setting_operation(self):
		# When a flag is set, remain in that state, until unset.
		while True:
			while self.set_left_score or self.set_right_score:
				self.display.clear_half(
					const.LEFT if self.set_left_score else const.RIGHT)
				await asyncio.sleep_ms(300)

				# Ensure no interrupts when reading/showing score
				self.receiver.disable_irq()
				self.display.show_score(self.left_score, self.right_score)
				self.receiver.enable_irq()
				await asyncio.sleep_ms(650)
			while self.set_day or self.set_month or self.set_year:
				if self.set_day:
					self.display.clear_quarter(const.TOP_LEFT)
				elif self.set_month:
					self.display.clear_quarter(const.TOP_RIGHT)
				else:
					# self.display.clear_matrix_row(const.BOTTOM_ROW)
					self.display.clear_quarter(const.BOTTOM_LEFT)
					self.display.clear_quarter(const.BOTTOM_RIGHT)
				await asyncio.sleep_ms(300)

				# Ensure no interrupts when reading/showing date
				self.receiver.disable_irq()
				self.display.show_date_setting(
					self.dt.date, self.dt.month, self.dt.year)
				self.receiver.enable_irq()
				await asyncio.sleep_ms(650)
			while self.set_hour or self.set_minute:
				self.display.clear_half(
					const.LEFT if self.set_hour else const.RIGHT)
				await asyncio.sleep_ms(300)

				# Ensure no interrupts when reading/showing time
				self.receiver.disable_irq()
				self.display.show_time(self.dt.hours, self.dt.minutes)
				self.receiver.enable_irq()
				await asyncio.sleep_ms(650)
			while self.set_brightness:
				if self.brightness_changed:
					self.display.set_brightness(self.brightness)
					self.display.show_brightness(self.brightness)
					self.brightness_changed = False

			# pass execution to other tasks
			await asyncio.sleep_ms(0)

	async def main(self):
		self.score = self.memory.get_last_score()
		self.config = self.memory.get_cfg()

		recv_pin = Pin(const.RECV_PIN, Pin.IN)
		# Set button_handler as remote control IRQ handler
		self.receiver = NEC_8(recv_pin, self.button_handler)

		# display config
		mx_spi = SPI(const.DISPLAY_SPI_ID, baudrate=const.DISPLAY_SPI_BAUD,
			polarity=const.DISPLAY_SPI_POLARITY, phase=const.DISPLAY_SPI_PHASE,
			sck=Pin(const.DISPLAY_SPI_CLK_PIN),
			mosi=Pin(const.DISPLAY_SPI_MOSI_PIN))
		cs_pin = Pin(const.DISPLAY_SPI_CS_PIN, Pin.OUT)
		self.display = Matrix(mx_spi, cs_pin, self.config.bright_lvl)

		# Real Time Clock & EEPROM config - same I2C bus
		rtc_mem_i2c = I2C(const.RTC_I2C_ID, sda=Pin(const.RTC_I2C_SDA_PIN, Pin.OPEN_DRAIN),
		    scl=Pin(const.RTC_I2C_SCL_PIN, Pin.OPEN_DRAIN), freq=400_000)
		self.clock = RTC(rtc_mem_i2c)
		self.memory = EEPROM(rtc_mem_i2c)

		self.ticks = utime.ticks_ms()

		asyncio.create_task(self.led_blink())
		asyncio.create_task(self.basic_operation())
		asyncio.create_task(self.setting_operation())
		asyncio.create_task(self.mem_monitor())

		# Run forever
		while True:
			await asyncio.sleep(10)


# Allocate buffer for exceptions during interrupt service routines
micropython.alloc_emergency_exception_buf(100)

try:
	app = App()
	asyncio.run(app.main())
except KeyboardInterrupt:
	print('Interrupted')
finally:
	asyncio.new_event_loop()  # Clear retained state

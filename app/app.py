# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

from machine import Pin
from lib.ir_rx.nec import NEC_8  # NEC remote, 8 bit addresses
from app.mx_data import MxDate, MxTime, MxScore, MxBrightness
from app.hw import display
from app.view import Viewer

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

		# Flags
		self.set_left_score = False
		self.set_right_score = False
		self.set_day = False
		self.set_month = False
		self.set_year = False
		self.set_hour = False
		self.set_minute = False
		self.set_brightness = False
		self.brightness_changed = False
		self.score_reset = False
		self.basic_mode = True
		self.is_on = False
		
		self.last_button = 0x00
		self.reset_score_cnt = 0

		recv_pin = Pin(const.RECV_PIN, Pin.IN)
		# Set button_handler as remote control IRQ handler
		self.receiver = NEC_8(recv_pin, self.button_handler)

		self.display = display

		# Count ticks for measuring period between button pushes
		self.ticks = utime.ticks_ms()

		# Info renderable on the matrix
		self.mx_score = MxScore()
		self.mx_bright = MxBrightness()
		self.mx_date = MxDate()
		self.mx_time = MxTime()

		self.viewer = Viewer(self.mx_score)

	def button_handler(self, button, addr, ctrl):
		if button == NEC_8.REPEAT:
			# Button Up/Down holding - repeated push
			if self.last_button in [const.BUTTON_UP, const.BUTTON_DOWN]:
				self.handle_regular_button(self.last_button)
			# Button 0 holding - potential score reset
			elif self.last_button == const.BUTTON_0:
				self.handle_score_reset()
		else:
			# reset hold button (reset score) counter
			self.reset_score_cnt = 0
			self.handle_regular_button(button)
			# Set new last pushed button for future potential repeat code button
			self.last_button = button

	def handle_regular_button(self, button):
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

	"""
	In basic mode, when the counter hits defined threshold, it is treated 
	as a signal	for reseting the whole score - the "reset score button" 
	was held for long enough time.
	"""
	def handle_score_reset(self):
		if self.basic_mode:
			if self.reset_score_cnt >= 6:
				self.mx_score.reset()
				self.reset_score_cnt = 0
				self.score_reset = True
				self.basic_mode = False
				print("Score reset to 0:0")
			else:
				self.reset_score_cnt += 1

	"""
	Execute the code conditionally.
	Avoid unwanted double increment/decrement of values
	- two changes of the same type in a very short time.
	"""
	def exec_not_too_fast(self, change):
		MIN_TICKS_DIFF = 200

		t_curr = utime.ticks_ms()
		t_diff = utime.ticks_diff(t_curr, self.ticks)
		executed = False
		# t_diff can also be negative, after a period of time
		if t_diff > MIN_TICKS_DIFF or t_diff < 0:
			self.ticks = t_curr
			# Execute the change itself
			change()
			executed = True
		return executed
	
	def handle_btn_0(self):
		if self.set_left_score:
			self.mx_score.set_left(0)
			self.mx_score.render()
			print("Left score set to 0")
		elif self.set_right_score:
			self.mx_score.set_right(0)
			self.mx_score.render()
			print("Right score set to 0")
		elif self.set_hour:
			self.mx_time.set_hours(0)
			self.mx_time.render()
			print("Hour reset set to 0")
		elif self.set_minute:
			self.mx_time.set_minutes(0)
			self.mx_time.render()
			print("Minute set to 0")
		elif self.set_brightness:
			self.mx_bright.set_lvl(0)
			self.brightness_changed = True
			print("Brightness set to 0")

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
			self.mx_date.pull()
			self.mx_date.render_setting()

	def handle_btn_left(self):
		if self.basic_mode:
			self.set_left_score = True
			self.basic_mode = False
			self.mx_score.render()
			print("Setting left score...")

	def handle_btn_right(self):
		if self.basic_mode:
			self.set_right_score = True
			self.basic_mode = False
			self.mx_score.render()
			print("Setting right score...")

	def handle_btn_up(self):
		if self.set_left_score:
			self.exec_not_too_fast(self.mx_score.incr_left)
			self.mx_score.render()
		elif self.set_right_score:
			self.exec_not_too_fast(self.mx_score.incr_right)
			self.mx_score.render()
		elif self.set_day:
			self.mx_date.incr_day()
			self.mx_date.render_setting()
		elif self.set_month:
			self.mx_date.incr_month()
			self.mx_date.render_setting()
		elif self.set_year:
			self.mx_date.incr_year()
			self.mx_date.render_setting()
		elif self.set_hour:
			self.mx_time.incr_hour()
			self.mx_time.render_setting()
		elif self.set_minute:
			self.mx_time.incr_minute()
			self.mx_time.render_setting()
		elif self.set_brightness:
			self.brightness_changed |= self.exec_not_too_fast(
				self.mx_bright.incr)

	def handle_btn_down(self):
		if self.set_left_score:
			self.exec_not_too_fast(self.mx_score.decr_left)
			self.mx_score.render()
		elif self.set_right_score:
			self.exec_not_too_fast(self.mx_score.decr_right)
			self.mx_score.render()
		elif self.set_day:
			self.mx_date.decr_day()
			self.mx_date.render_setting()
		elif self.set_month:
			self.mx_date.decr_month()
			self.mx_date.render_setting()
		elif self.set_year:
			self.mx_date.decr_year()
			self.mx_date.render_setting()
		elif self.set_hour:
			self.mx_time.decr_hour()
			self.mx_time.render_setting()
		elif self.set_minute:
			self.mx_time.decr_minute()
			self.mx_time.render_setting()
		elif self.set_brightness:
			self.brightness_changed |= self.exec_not_too_fast(
				self.mx_bright.decr)

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
		self.display.reinit_display(self.mx_bright.get_lvl())

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
			self.mx_date.validate_max_days()
		elif self.set_year:
			self.mx_date.push()
			self.set_year = False
			self.set_hour = True
		elif self.set_hour:
			self.set_hour = False
			self.set_minute = True
			print("Hour set!")
		elif self.set_minute:
			self.mx_time.push()
			self.set_minute = False
			self.basic_mode = True
			print("Minute set!")
		elif self.set_brightness:
			self.mx_bright.save()
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
				self.viewer.enable()
				# if self.nv_mem.get_cfg().scroll:
				if True:
					await self.viewer.scroll()
				else:
					# Ensure no interrupts when reading/showing score
					self.receiver.disable_irq()
					self.mx_score.render()
					self.receiver.enable_irq()
					await asyncio.sleep_ms(3000)

					# Need to check again if still valid
					if self.basic_mode:
						self.mx_time.pull()
						self.mx_time.render()
						await asyncio.sleep_ms(2000)
			# pass execution to other tasks
			await asyncio.sleep_ms(0)

	async def scroll_info(self):
		info_len = 12 * const.COLS_IN_MATRIX + 8
		info_len = 5 * const.COLS_IN_MATRIX

		for x_shift in range(32, -info_len, -1):
			if not self.basic_mode:
				break
			
			self.mx_time.pull()
			self.mx_time.render(x_shift)

			await asyncio.sleep_ms(30)

	async def setting_operation(self):
		# When a flag is set, remain in that state, until unset.
		while True:
			while self.set_left_score or self.set_right_score:
				self.viewer.disable()
				self.display.clear_half(
					const.LEFT if self.set_left_score else const.RIGHT)
				await asyncio.sleep_ms(300)

				# Ensure no interrupts when reading/showing score
				self.receiver.disable_irq()
				self.mx_score.render()
				self.receiver.enable_irq()
				await asyncio.sleep_ms(650)
			while self.set_day or self.set_month or self.set_year:
				self.viewer.disable()
				if self.set_day:
					self.display.clear_quarter(const.TOP_LEFT)
				elif self.set_month:
					self.display.clear_quarter(const.TOP_RIGHT)
				else:
					self.display.clear_matrix_row(const.BOTTOM_ROW)
				await asyncio.sleep_ms(300)

				# Ensure no interrupts when reading/showing date
				self.receiver.disable_irq()
				self.mx_date.render_setting()
				self.receiver.enable_irq()
				await asyncio.sleep_ms(650)
			while self.set_hour or self.set_minute:
				self.viewer.disable()
				self.display.clear_half(
					const.LEFT if self.set_hour else const.RIGHT)
				await asyncio.sleep_ms(300)

				# Ensure no interrupts when reading/showing time
				self.receiver.disable_irq()
				self.mx_time.render_setting()
				self.receiver.enable_irq()
				await asyncio.sleep_ms(650)
			while self.set_brightness:
				self.viewer.disable()
				if self.brightness_changed:
					self.mx_bright.mx_set()
					self.mx_bright.render()
					self.brightness_changed = False
			if self.score_reset:
				self.viewer.disable()
				self.mx_score.render()
				# Pause for some time before re-enabling basic mode again
				await asyncio.sleep_ms(1500)
				self.score_reset = False
				self.basic_mode = True

			# pass execution to other tasks
			await asyncio.sleep_ms(0)

	async def main(self):
		asyncio.create_task(self.led_blink())
		asyncio.create_task(self.basic_operation())
		asyncio.create_task(self.setting_operation())
		# asyncio.create_task(self.mem_monitor())

		print('Running')

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

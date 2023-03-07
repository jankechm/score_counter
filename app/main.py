# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

from machine import Pin
from lib.ir_rx.nec import NEC_8  # NEC remote, 8 bit addresses
from app.mx_data import MxDate, MxTime, MxScore, MxBrightness
from app.hw import display
from app.view import BasicViewer, SettingsViewer
from app.mx_data import MxUseScoreCfg, MxUseDateCfg, MxUseTimeCfg, MxUseTemperatureCfg, MxUseScrollingCfg

import uasyncio as asyncio
import app.constants as const

import micropython
import utime
import gc

class App:
	HOLD_BTN_RPT_THRESHOLD = 6

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
		self.set_score_cfg = False
		self.set_date_cfg = False
		self.set_time_cfg = False
		self.set_temperature_cfg = False
		self.set_scrolling_cfg = False
		self.set_day = False
		self.set_month = False
		self.set_year = False
		self.set_hour = False
		self.set_minute = False
		self.set_brightness = False
		self.brightness_changed = False
		self.score_reset = False
		self.revert_score = False
		self.exit = False
		self.basic_mode = True
		self.display_on = True
		
		self.last_button = 0x00
		self.reset_score_cnt = 0
		self.revert_score_cnt = 0
		self.exit_cnt = 0

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

		# Settings renderable on the matrix
		self.mx_use_score_cfg = MxUseScoreCfg()
		self.mx_use_date_cfg = MxUseDateCfg()
		self.mx_use_time_cfg = MxUseTimeCfg()
		self.mx_use_temperature = MxUseTemperatureCfg()
		self.mx_use_scrolling = MxUseScrollingCfg()

		self.basic_viewer = BasicViewer()
		self.basic_viewer.score = self.mx_score  # type: ignore
		self.settings_viewer = SettingsViewer()

	def button_handler(self, button, addr, ctrl):
		if button == NEC_8.REPEAT:
			# Button Up/Down holding - repeated push
			# Button 0 holding - potential score reset
			# Button Down holding - potential score revert
			# Button OK holding - exit program
			if self.last_button in [
				const.BUTTON_UP, const.BUTTON_DOWN, 
				const.BUTTON_0, const.BUTTON_OK]:
				self.handle_single_push_btn(self.last_button)
		else:
			# reset hold button counters
			self.reset_score_cnt = 0
			self.revert_score_cnt = 0

			self.handle_single_push_btn(button)
			# Set new last pushed button for future potential repeat code button
			self.last_button = button

	def handle_single_push_btn(self, button):
		if button == const.BUTTON_0:
			self.handle_btn_0()
		elif button == const.BUTTON_3:
			self.handle_btn_3()
		elif button == const.BUTTON_4:
			self.handle_btn_4()
		elif button == const.BUTTON_5:
			self.handle_btn_5()
		elif button == const.BUTTON_6:
			self.handle_btn_6()
		elif button == const.BUTTON_7:
			self.handle_btn_7()
		elif button == const.BUTTON_8:
			self.handle_btn_8()
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

	def exec_not_too_fast(self, change):
		"""
		Execute the code conditionally.
		Avoid unwanted double increment/decrement of values
		- two changes of the same type in a very short time.
		"""
		
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
		"""
		Reset something to 0.
		"""

		if self.basic_mode:
			"""
			In basic mode, when the "reset score button" was held
			for long enough time, it is treated as a signal for resetting
			the whole score.
			Long enough time means that the reset score counter hits
			defined threshold.
			"""
			if self.reset_score_cnt >= self.HOLD_BTN_RPT_THRESHOLD:
				self.reset_score_cnt = 0
				self.score_reset = True
				self.basic_mode = False
				print("Score reset to 0:0")
			else:
				self.reset_score_cnt += 1
		else:
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

	def handle_btn_3(self):
		"""
		Score usage
		"""

		if self.basic_mode:
			self.set_score_cfg = True
			self.basic_mode = False
			print("Setting score usage...")
	
	def handle_btn_4(self):
		"""
		Date usage
		"""

		if self.basic_mode:
			self.set_date_cfg = True
			self.basic_mode = False
			print("Setting date usage...")

	def handle_btn_5(self):
		"""
		Time usage
		"""

		if self.basic_mode:
			self.set_time_cfg = True
			self.basic_mode = False
			print("Setting time usage...")

	def handle_btn_6(self):
		"""
		Temperature usage
		"""

		if self.basic_mode:
			self.set_temperature_cfg = True
			self.basic_mode = False
			print("Setting temperature usage...")

	def handle_btn_7(self):
		"""
		Scrolling usage
		"""

		if self.basic_mode:
			self.set_scrolling_cfg = True
			self.basic_mode = False
			print("Setting scrolling...")

	def handle_btn_8(self):
		"""
		Date & time
		"""

		if self.basic_mode:
			self.set_day = True
			self.basic_mode = False
			self.mx_date.pull()
			self.mx_date.render_setting()

	def handle_btn_9(self):
		"""
		Brightness
		"""

		if self.basic_mode:
			self.set_brightness = True
			self.brightness_changed = True
			self.basic_mode = False
			print("Setting brightness...")

	def handle_btn_left(self):
		"""
		Left score
		"""

		if self.basic_mode:
			self.set_left_score = True
			self.basic_mode = False
			self.mx_score.render()
			print("Setting left score...")

	def handle_btn_right(self):
		"""
		Right score
		"""

		if self.basic_mode:
			self.set_right_score = True
			self.basic_mode = False
			self.mx_score.render()
			print("Setting right score...")

	def handle_btn_up(self):
		"""
		Increment or enable something.
		"""

		if self.set_left_score:
			self.exec_not_too_fast(self.mx_score.incr_left)
			self.mx_score.render()
		elif self.set_right_score:
			self.exec_not_too_fast(self.mx_score.incr_right)
			self.mx_score.render()
		elif self.set_score_cfg:
			self.mx_use_score_cfg.use_it = True
		elif self.set_date_cfg:
			self.mx_use_date_cfg.use_it = True
		elif self.set_time_cfg:
			self.mx_use_time_cfg.use_it = True
		elif self.set_temperature_cfg:
			self.mx_use_temperature.use_it = True
		elif self.set_scrolling_cfg:
			self.mx_use_scrolling.use_it = True
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
		"""
		Decrement or disable or revert something.
		"""
		
		if self.basic_mode:
			"""
			In basic mode, when the "revert score button" was held
			for long enough time, it is treated as a signal for setting
			the score to it's previous value (the last operation is undone, e.g.
			if the left side was incremented by 1, it is being decremented by 1).
			Long enough time means that the revert score counter hits
			defined threshold.
			"""
			if self.revert_score_cnt >= self.HOLD_BTN_RPT_THRESHOLD:
				self.revert_score_cnt = 0
				self.revert_score = True
				self.basic_mode = False
				print("Reverting score...")
			else:
				self.revert_score_cnt += 1
		else:
			if self.set_left_score:
				self.exec_not_too_fast(self.mx_score.decr_left)
				self.mx_score.render()
			elif self.set_right_score:
				self.exec_not_too_fast(self.mx_score.decr_right)
				self.mx_score.render()
			elif self.set_score_cfg:
				self.mx_use_score_cfg.use_it = False
			elif self.set_date_cfg:
				self.mx_use_date_cfg.use_it = False
			elif self.set_time_cfg:
				self.mx_use_time_cfg.use_it = False
			elif self.set_temperature_cfg:
				self.mx_use_temperature.use_it = False
			elif self.set_scrolling_cfg:
				self.mx_use_scrolling.use_it = False
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
		"""
		Display on/off.
		"""

		if self.display_on:
			print("Off")
			self.display.turn_off()
			self.display_on = False
		else:
			print("On")
			self.display.turn_on()
			self.display_on = True

	def handle_btn_hash(self):
		"""
		Reinitialize display.
		"""

		print("Resetting display...")
		self.display.reinit_display(self.mx_bright.get_lvl())

	def handle_btn_ok(self):
		"""
		Confirm some setting.
		"""

		if self.basic_mode:
			"""
			In basic mode, when the "OK button" was held
			for long enough time, it is treated as a signal to exit
			from the main program execution.
			Long enough time means that exit counter hits
			defined threshold.
			"""
			if self.exit_cnt >= self.HOLD_BTN_RPT_THRESHOLD:
				self.exit_cnt = 0
				self.exit = True
				self.basic_mode = False
				print("Reverting score...")
			else:
				self.exit_cnt += 1
		else:
			if self.set_left_score:
				self.mx_score.save()
				self.set_left_score = False
				self.basic_mode = True
				print("Left score set!")
			elif self.set_right_score:
				self.mx_score.save()
				self.set_right_score = False
				self.basic_mode = True
				print("Right score set!")
			elif self.set_score_cfg:
				self.mx_use_score_cfg.save()
				self.set_score_cfg = False
				self.basic_mode = True
				print("Score usage set!")
			elif self.set_date_cfg:
				self.mx_use_date_cfg.save()
				self.set_date_cfg = False
				self.basic_mode = True
				print("Date usage set!")
			elif self.set_time_cfg:
				self.mx_use_time_cfg.save()
				self.set_time_cfg = False
				self.basic_mode = True
				print("Time usage set!")
			elif self.set_temperature_cfg:
				self.mx_use_temperature.save()
				self.set_temperature_cfg = False
				self.basic_mode = True
				print("Temperature usage set!")
			elif self.set_scrolling_cfg:
				self.mx_use_scrolling.save()
				self.set_scrolling_cfg = False
				self.basic_mode = True
				print("Scrolling set!")
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
				self.settings_viewer.disable()

				await self.basic_viewer.view_info()
			# pass execution to other tasks
			await asyncio.sleep_ms(0)

	async def setting_operation(self):
		# When a flag is set, remain in that state, until unset.
		while True:
			if not self.basic_mode:
				self.basic_viewer.disable()

				while self.set_left_score or self.set_right_score:
					self.display.clear_half(
						const.LEFT if self.set_left_score else const.RIGHT)
					await asyncio.sleep_ms(300)

					# Ensure no interrupts when reading/showing score
					self.receiver.disable_irq()
					self.mx_score.render()
					self.receiver.enable_irq()
					await asyncio.sleep_ms(650)
				while self.set_score_cfg:
					await self.settings_viewer.scroll_score_cfg()
				while self.set_date_cfg:
					await self.settings_viewer.scroll_date_cfg()
				while self.set_time_cfg:
					await self.settings_viewer.scroll_time_cfg()
				while self.set_temperature_cfg:
					await self.settings_viewer.scroll_temperature_cfg()
				while self.set_scrolling_cfg:
					await self.settings_viewer.scroll_scrolling_cfg()
				while self.set_day or self.set_month or self.set_year:
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
					self.display.clear_half(
						const.LEFT if self.set_hour else const.RIGHT)
					await asyncio.sleep_ms(300)

					# Ensure no interrupts when reading/showing time
					self.receiver.disable_irq()
					self.mx_time.render_setting()
					self.receiver.enable_irq()
					await asyncio.sleep_ms(650)
				while self.set_brightness:
					if self.brightness_changed:
						self.mx_bright.mx_set()
						self.mx_bright.render()
						self.brightness_changed = False
				if self.score_reset:
					self.mx_score.reset()
					self.mx_score.render()
					# Pause for some time before re-enabling basic mode again
					await asyncio.sleep_ms(1500)
					self.score_reset = False
					self.basic_mode = True
				if self.revert_score:
					self.receiver.disable_irq()

					self.mx_score.render()
					await asyncio.sleep_ms(400)
					side = self.mx_score.get_last_changed_side()
					self.display.clear_half(side)
					await asyncio.sleep_ms(300)
					self.mx_score.render()
					await asyncio.sleep_ms(400)
					self.mx_score.revert()
					self.mx_score.render()
					await asyncio.sleep_ms(900)

					self.receiver.enable_irq()
					self.revert_score = False
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
		while not self.exit:
			await asyncio.sleep(2)

		print('Exit')


# Allocate buffer for exceptions during interrupt service routines
micropython.alloc_emergency_exception_buf(100)

try:
	app = App()
	asyncio.run(app.main())
except KeyboardInterrupt:
	print('Interrupted')
finally:
	asyncio.new_event_loop()  # Clear retained state

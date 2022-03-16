# Author: Marek Jankech
# Copyright Marek Jankech 2022 Released under the MIT license

from machine import Pin, SPI
from utime import sleep_ms
from app.char import Char
from app.struct import datetime

import app.constants as const
import app.font as mx_font

import framebuf

class Matrix:
	WIDTH = const.MATRIXES_IN_ROW * const.COLS_IN_MATRIX
	HEIGHT = const.MATRIXES_IN_COL * const.ROWS_IN_MATRIX
	HALF_WIDTH = WIDTH // 2
	HALF_HEIGHT = const.ROWS_IN_MATRIX
	BOTTOM_HALF_OFFSET = const.MATRIXES_IN_ROW * const.ROWS_IN_MATRIX

	def __init__(self, spi: SPI, cs_pin: Pin):
		"""
		Provides operations for showing patterns on matrix display.
		"""
		self.spi = spi
		self.cs_pin = cs_pin

		self.buffer = bytearray(
			const.ROWS_IN_MATRIX * const.MATRIXES_IN_ROW * const.MATRIXES_IN_COL)

		self.fb = framebuf.FrameBuffer(self.buffer, 
			const.COLS_IN_MATRIX * const.MATRIXES_IN_ROW,
			const.ROWS_IN_MATRIX * const.MATRIXES_IN_COL, framebuf.MONO_HLSB)

		self.init_display()

	def init_display(self):
		self._write(const.SHUTDOWN, const.SHUTDOWN_MODE_ON)

		self._write(const.DISPLAYTEST, const.DISPLAY_TEST_ON)
		sleep_ms(300)
		self._write(const.DISPLAYTEST, const.DISPLAYTEST_TEST_OFF)

		self._write(const.SCANLIMIT, const.SCANLIMIT_8_DIGITS)
		self._write(const.DECODEMODE, const.NO_BCD_DECODE)
		self._write(const.INTENSITY, const.INITIAL_BRIGHTNESS)

		self._write(const.SHUTDOWN, const.SHUTDOWN_MODE_OFF)

	def turn_off(self):
		self._write(const.SHUTDOWN, const.SHUTDOWN_MODE_ON)

	def turn_on(self):
		self._write(const.SHUTDOWN, const.SHUTDOWN_MODE_OFF)

	def set_brightness(self, val):
		if val > 3:
			val = 3
		elif val < 0:
			val = 0

		self._write(const.INTENSITY, val)

	def redraw(self):
		for row_idx in range(const.ROWS_IN_MATRIX):
			self.cs_pin.value(0)

			# First half of the buffer
			for matrix_idx in range(const.MATRIXES_IN_ROW):
				self.spi.write(bytearray([const.ROW0 + row_idx, 
					self.buffer[(row_idx * const.MATRIXES_IN_ROW) + matrix_idx]]))

			# Second half of the buffer
			for matrix_idx in range(const.MATRIXES_IN_ROW):
				self.spi.write(bytearray([const.ROW0 + row_idx, 
					self.buffer[(row_idx * const.MATRIXES_IN_ROW) + matrix_idx
					+ Matrix.BOTTOM_HALF_OFFSET]]))

			self.cs_pin.value(1)

	def show_score(self, left_score: int, right_score: int):
		# at first, clear framebuffer
		self.fb.fill(0)

		self._render_score(left_score, False)
		self._render_score_delimiter()
		self._render_score(right_score, True)

		self.redraw()
		# Some LEDs need to tell it twice to understand...
		self.redraw()

	def show_time(self, hour: int, minute: int):
		# at first, clear framebuffer
		self.fb.fill(0)

		(h_tens, h_ones) = divmod(hour, 10)
		(m_tens, m_ones) = divmod(minute, 10)

		font = mx_font.MediumDigit()

		self._render_2_digits_medium(font.get(h_tens), font.get(h_ones),
				(h_ones == 1), False)
		self._render_time_delimiter(0)
		self._render_2_digits_medium(font.get(m_tens), font.get(m_ones),
				(m_ones == 1), True)

		self.redraw()
		# Some LEDs need to tell it twice to understand...
		self.redraw()

	def show_date_setting(self, day, month, year):
		# at first, clear framebuffer
		self.fb.fill(0)

		self.fb.text("{:02d}{:02d}".format(day, month), 0, 0)
		self.fb.text(str(year), 0, 8)

		self._render_date_setting_ordinal_dots(0)

		self.redraw()
		# Some LEDs need to tell it twice to understand...
		self.redraw()

	def show_variable_info(self, x_shift: int, dt: datetime, celsius=-1):
		cursor = 0
		font = mx_font.Medium()

		self.fb.fill(0)

		# -1 treated as date is not used
		if -1 not in [dt.date, dt.month]:
			cursor = self._render_date(
				dt.date, dt.month, x_shift, cursor, font)

		if -1 not in [dt.hours, dt.minutes]:
			cursor = self._render_time(
				dt.hours, dt.minutes, x_shift, cursor, font)

		if celsius != -1:
			self._render_temperature(celsius, cursor, x_shift, font)

		self.redraw()
		# Some LEDs need to tell it twice to understand...
		self.redraw()

	def _render_temperature(self, celsius, cursor, x_shift, font):
		self._render_2_digit_num(celsius, cursor + x_shift, font)
		cursor += 2 * const.COLS_IN_MATRIX

		degree = font.get("°")
		degree.x_shift(cursor + x_shift)
		degree.render(self.fb)
		cursor += const.COLS_IN_MATRIX

		c_char = font.get("C")
		c_char.x_shift(cursor + x_shift)
		c_char.render(self.fb)
		cursor += const.COLS_IN_MATRIX

		return cursor

	def show_brightness(self, level):
		# at first, clear framebuffer
		self.fb.fill(0)

		# self.fb.text("jas{}".format(level), 0, 0, 1)
		self._render_brightness(level)

		self.redraw()
		# Some LEDs need to tell it twice to understand...
		self.redraw()

	def clear_half(self, side):
		if side == const.LEFT:
			self.fb.fill_rect(0, 0, Matrix.HALF_WIDTH - 1, Matrix.HEIGHT, 0)
		else:
			self.fb.fill_rect(Matrix.HALF_WIDTH + 1, 0, Matrix.HALF_WIDTH - 1,
				Matrix.HEIGHT, 0)

		self.redraw()
		self.redraw()

	def clear_quarter(self, quarter):
		if quarter == const.TOP_LEFT:
			self.fb.fill_rect(0, 0, Matrix.HALF_WIDTH, Matrix.HALF_HEIGHT, 0)
		elif quarter == const.TOP_RIGHT:
			self.fb.fill_rect(Matrix.HALF_WIDTH, 0, Matrix.HALF_WIDTH,
				Matrix.HALF_HEIGHT, 0)
		elif quarter == const.BOTTOM_LEFT:
			self.fb.fill_rect(0, Matrix.HALF_HEIGHT, Matrix.HALF_WIDTH,
				Matrix.HALF_HEIGHT, 0)
		else:
			self.fb.fill_rect(Matrix.HALF_WIDTH, Matrix.HALF_HEIGHT,
				Matrix.HALF_WIDTH, Matrix.HALF_HEIGHT, 0)

		self.redraw()
		self.redraw()

	def clear_matrix_row(self, row):
		if row == const.TOP_ROW:
			self.fb.fill_rect(0, 0, Matrix.WIDTH, Matrix.HALF_HEIGHT, 0)
		else:
			self.fb.fill_rect(0, Matrix.HALF_HEIGHT, Matrix.WIDTH,
				Matrix.HALF_HEIGHT, 0)

	def _write(self, register_add, data):
		self.cs_pin.value(0)
		
		for _ in range(const.CASCADED_MATRIXES):
			self.spi.write(bytearray([register_add, data]))
		
		self.cs_pin.value(1)

	def _render_score_delimiter(self):
		self.fb.hline(15, 7, 2, 1)
		self.fb.hline(15, 8, 2, 1)

	def _render_time_delimiter(self, x_shift):
		self.fb.hline(15 + x_shift, 4, 2, 1)
		self.fb.hline(15 + x_shift, 5, 2, 1)
		self.fb.hline(15 + x_shift, 10, 2, 1)
		self.fb.hline(15 + x_shift, 11, 2, 1)

	def _render_date_setting_ordinal_dots(self, x_shift):
		self.fb.pixel(15 + x_shift, 7, 1)
		self.fb.pixel(31 + x_shift, 7, 1)

	def _render_date_ordinal_dots(self, x_shift):
		self.fb.pixel(15 + x_shift, 15, 1)
		self.fb.pixel(31 + x_shift, 15, 1)

	def _render_score(self, score: int, is_right_side: bool):
		(tens, ones) = divmod(score, 10)
		ones_is_1 = (ones == 1)

		font = mx_font.BigDigit()

		if tens == 0:
			self._render_1_digit(font.get(ones), ones_is_1, is_right_side)
		elif tens == 1:
			self._render_2_digits(font.get(tens), font.get(ones), ones_is_1,
			 	is_right_side)
		else:
			font = mx_font.MediumDigit()
			self._render_2_digits_medium(font.get(tens), font.get(ones),
				ones_is_1, is_right_side)

	def _render_1_digit(self, digit: Char, digit_is_1: bool, is_right_side: bool):
		total_offset = self._get_right_side_offset(is_right_side, False)

		if digit_is_1:
			total_offset += const.ONE_DIGIT_IS_1_X_OFFSET
		else:
			total_offset += const.ONE_DIGIT_X_OFFSET

		digit.x_shift(total_offset)
		digit.render(self.fb)

	def _render_2_digits(self, digit1, digit2, digit2_is_1: bool, is_right_side: bool):
		right_side_offset = self._get_right_side_offset(is_right_side, False)
		digit1_total_offset = const.FIRST_DIGIT_X_OFFSET + right_side_offset
		digit2_total_offset = right_side_offset

		if digit2_is_1:
			digit2_total_offset += const.SECOND_DIGIT_IS_1_X_OFFSET
		else:
			digit2_total_offset += const.SECOND_DIGIT_X_OFFSET

		digit1.x_shift(digit1_total_offset)
		digit1.render(self.fb)

		digit2.x_shift(digit2_total_offset)
		digit2.render(self.fb)

	def _render_2_digits_medium(self, digit1, digit2, digit2_is_1: bool, is_right_side: bool):
		right_side_offset = self._get_right_side_offset(is_right_side, True)
		digit2_total_offset = right_side_offset

		if digit2_is_1:
			digit2_total_offset += const.SECOND_DIGIT_IS_1_X_OFFSET
		else:
			digit2_total_offset += const.SECOND_DIGIT_MEDIUM_FONT_X_OFFSET

		digit1.x_shift(right_side_offset)
		digit1.render(self.fb)

		digit2.x_shift(digit2_total_offset)
		digit2.render(self.fb)

	def _render_date(self, day, month, x_shift, cursor, font):
		self._render_2_digit_num(day, cursor + x_shift, font)
		cursor += 2 * const.COLS_IN_MATRIX - 1

		# ordinal dot
		self.fb.hline(cursor + x_shift, 13, 2, 1)
		self.fb.hline(cursor + x_shift, 14, 2, 1)
		cursor += 3
		
		self._render_2_digit_num(month, cursor + x_shift, font)
		cursor += 2 * const.COLS_IN_MATRIX - 1

		# ordinal dot
		self.fb.hline(cursor + x_shift, 13, 2, 1)
		self.fb.hline(cursor + x_shift, 14, 2, 1)
		# shift cursor for ordinal dot + space
		cursor += 3 + const.COLS_IN_MATRIX

		return cursor

	def _render_time(self, hour, minute, x_shift, cursor, font):
		self._render_2_digit_num(hour, cursor + x_shift, font)
		cursor += 2 * const.COLS_IN_MATRIX

		self._render_time_delimiter(cursor + x_shift - 16)
		cursor += 2

		self._render_2_digit_num(minute, cursor + x_shift, font)
		# 2 digits + space
		cursor += 3 * const.COLS_IN_MATRIX

		return cursor

	def _render_2_digit_num(self, num, x_shift, font):
		(tens, ones) = divmod(num, 10)

		for digit in [tens, ones]:
			char = font.get(str(digit))
			char.x_shift(x_shift)
			char.render(self.fb)

			x_shift += const.COLS_IN_MATRIX

	def _render_brightness(self, level: int):
		alpha_font = mx_font.Medium()

		j_char = alpha_font.get("J")
		a_char = alpha_font.get("A")
		s_char = alpha_font.get("S")
		lvl_char = alpha_font.get(str(level))

		a_char.x_shift(const.COLS_IN_MATRIX)
		s_char.x_shift(const.COLS_IN_MATRIX * 2)
		lvl_char.x_shift(const.COLS_IN_MATRIX * 3)

		j_char.render(self.fb)
		a_char.render(self.fb)
		s_char.render(self.fb)
		lvl_char.render(self.fb)

	def _get_right_side_offset(self, is_right_side: bool, is_medium_font: bool):
		if is_right_side:
			if is_medium_font:
				offset = const.RIGHT_SIDE_MEDIUM_FONT_X_OFFSET
			else:
				offset = const.RIGHT_SIDE_X_OFFSET
		else:
			offset = 0

		return offset

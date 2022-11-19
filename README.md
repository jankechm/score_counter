# Electronic score counter and clock on a matrix display.
- The display consists of eight 8*8 LED matrixes controlled by MAX7219.
- DS3231 is used as a Real Time Clock.
- Configuration and actual + previous score is stored on AT24C32 EEPROM memory.
- IR remote control with NEC protocol is used to send commands (the plan is to replace it by bluetooth modules).
- The code runs on RP2040 MCU (Raspberry Pi Pico) with installed micropython interpreter.

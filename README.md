# Electronic score counter and clock on a matrix display.
- The display consists of eight 8*8 LED matrixes controlled by MAX7219.
- DS3231 is used as a Real Time Clock.
- Configuration and actual + previous score is stored on AT24C32 EEPROM memory.
- IR remote control with NEC protocol is used to send commands.
- The code runs on RP2040 MCU (Raspberry Pi Pico) with installed micropython interpreter.

https://github.com/jankechm/score_counter/assets/22982620/1a510b1c-4cc3-4e5c-9afb-9124423c3265

There is a new project https://github.com/jankechm/BLE-Score-Counter-Display which uses Bluetooth Low Energy and a smartphone app instead of IR remote control. Also, the external DS3231 RTC module was removed since the time is synchronized with smartphone and then counted by the internal RTC.

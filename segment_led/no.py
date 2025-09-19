import adafruit_ht16k33.segments

import board

import time

i2c = board.I2C()

display = adafruit_ht16k33.segments.Seg14x4(i2c)

while True:
    display.fill(0)
    display.show()
    time.sleep(0.3)
    display.print("*NE*")
    display.show()
    time.sleep(0.3)

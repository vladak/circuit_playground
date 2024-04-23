# SPDX-FileCopyrightText: 2022 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
from rainbowio import colorwheel
import neopixel

from adafruit_seesaw import seesaw, rotaryio, digitalio

INITIAL_COLOR = 16 # start at warm yellow
NUMPIXELS = 30  # Update this to match the number of LEDs.
SPEED = 0.3  # Increase to slow down the rainbow. Decrease to speed it up.
MIN_BRIGHTNESS = 0.2  # A number between 0.0 and 1.0, where 0.0 is off, and 1.0 is max.
PIN = board.A3  # This is the default pin on the 5x5 NeoPixel Grid BFF.

pixels = neopixel.NeoPixel(PIN, NUMPIXELS,
                           brightness=MIN_BRIGHTNESS, auto_write=False)

i2c = board.STEMMA_I2C()
seesaw1 = seesaw.Seesaw(i2c, addr=0x36)
seesaw2 = seesaw.Seesaw(i2c, addr=0x37)

seesaw1.pin_mode(24, seesaw1.INPUT_PULLUP)
seesaw2.pin_mode(24, seesaw2.INPUT_PULLUP)

button1 = digitalio.DigitalIO(seesaw1, 24)
button1_held = False
button2 = digitalio.DigitalIO(seesaw2, 24)
button2_held = False

encoder1 = rotaryio.IncrementalEncoder(seesaw1)
last_position1 = -1
encoder2 = rotaryio.IncrementalEncoder(seesaw2)
last_position2 = -1

def rainbow():
    """
    cycle through rainbox. for testing.
    """
    for color in range(255):
        for pixel in range(len(pixels)):  # pylint: disable=consider-using-enumerate
            pixel_index = (pixel * 256 // len(pixels)) + color * 5
            pixels[pixel] = colorwheel(pixel_index & 255)

        pixels.show()


def set_color(color):
    """
    set all pixels to given color.
    """
    print(f"Color -> {color}")
    for pixel in range(len(pixels)):  # pylint: disable=consider-using-enumerate
        pixels[pixel] = colorwheel(color)

    pixels.show()


color = INITIAL_COLOR

on = True  # whether the pixels are on/off
orig_brightness = None

while True:
    # negate the position to make clockwise rotation positive
    position1 = -encoder1.position
    position2 = -encoder2.position

    if on and position1 != last_position1:
        print("Position 1: {}".format(position1))

	if position1 > last_position1:  # Advance forward through the colorwheel.
            color += 1
        else:
            color -= 1  # Advance backward through the colorwheel.
	color = (color + 256) % 256  # wrap around to 0-256

	set_color(color)

        last_position1 = position1

    if on and position2 != last_position2:
        print("Position 2: {}".format(position2))

	if position2 > last_position2:  # Increase the brightness.
            new_brightness = min(1.0, pixels.brightness + 0.1)
        else:  # Decrease the brightness.
            new_brightness = max(MIN_BRIGHTNESS, pixels.brightness - 0.1)

	print(f"Brightness -> {new_brightness}")
	pixels.brightness = new_brightness
	pixels.show()

        last_position2 = position2

    if on and not button1.value and not button1_held:
        button_held1 = True
        print("Button 1 pressed")
	time.sleep(SPEED)

	set_color(INITIAL_COLOR)

    if not button2.value and not button2_held:
        button_held2 = True
        print("Button 2 pressed")
	time.sleep(SPEED)

	if on:
	   on = False
	   new_brightness = 0
	   orig_brightness = pixels.brightness
	else:
	   on = True
	   if orig_brightness:
	       new_brightness = orig_brightness
	   else:
	       new_brightness = MIN_BRIGHTNESS

	print(f"Brightness -> {new_brightness}")
	pixels.brightness = new_brightness
	pixels.show()

	# The sleep seems to be necessary to avoid registering multiple
	# press events for single physical press.
	time.sleep(SPEED)

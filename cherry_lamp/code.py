"""
LED strip controlled by 2 potentiometers (color, intensity)
"""

# SPDX-FileCopyrightText: 2022 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import traceback

import board
import microcontroller
import neopixel
import supervisor
from adafruit_seesaw import digitalio, rotaryio, seesaw

# pylint: disable=no-name-in-module
from microcontroller import watchdog
from rainbowio import colorwheel
from watchdog import WatchDogMode, WatchDogTimeout

INITIAL_COLOR = 16  # start at warm yellow
NUMPIXELS = 30  # Update this to match the number of LEDs.
SPEED = 0.3  # Increase to slow down the rainbow. Decrease to speed it up.
MIN_BRIGHTNESS = 0.2  # A number between 0.0 and 1.0, where 0.0 is off, and 1.0 is max.
PIN = board.A3  # This is the default pin on the 5x5 NeoPixel Grid BFF.
ESTIMATED_RUN_TIME = 1  # maximum time in seconds for the main loop iteration


def set_color(pixels, color):
    """
    set all pixels to given color.
    """
    print(f"Color -> {color}")
    for pixel in range(len(pixels)):  # pylint: disable=consider-using-enumerate
        pixels[pixel] = colorwheel(color)

    pixels.show()


def main():
    """
    main loop to check for potentiometer turns/presses
    """
    color = INITIAL_COLOR

    on = True  # whether the pixels are on/off
    orig_brightness = None

    print("running")

    watchdog.timeout = 10
    watchdog.mode = WatchDogMode.RAISE

    pixels = neopixel.NeoPixel(
        PIN, NUMPIXELS, brightness=MIN_BRIGHTNESS, auto_write=False
    )

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

    watchdog.feed()

    # reinit the watchdog for the main loop
    watchdog.mode = None
    watchdog.timeout = ESTIMATED_RUN_TIME
    watchdog.mode = WatchDogMode.RAISE

    while True:
        # logger.debug("loop")

        # negate the position to make clockwise rotation positive
        position1 = -encoder1.position
        position2 = -encoder2.position

        if on and position1 != last_position1:
            print(f"Position 1: {position1}")

            if position1 > last_position1:  # Advance forward through the colorwheel.
                color += 1
            else:
                color -= 1  # Advance backward through the colorwheel.
            color = (color + 256) % 256  # wrap around to 0-256

            set_color(pixels, color)

            last_position1 = position1

        if on and position2 != last_position2:
            print(f"Position 2: {position2}")

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

            set_color(pixels, INITIAL_COLOR)

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

        watchdog.feed()


def hard_reset(exception):
    """
    Sometimes soft reset is not enough. Perform hard reset.
    """
    watchdog.mode = None
    print(f"Got exception: {exception}")
    reset_time = 15
    print(f"Performing hard reset in {reset_time} seconds")
    time.sleep(reset_time)
    microcontroller.reset()  # pylint: disable=no-member


try:
    main()
except ConnectionError as e:
    # When this happens, it usually means that the microcontroller's wifi/networking is botched.
    # The only way to recover is to perform hard reset.
    hard_reset(e)
except MemoryError as e:
    # This is usually the case of delayed exception from the 'import wifi' statement,
    # possibly caused by a bug (resource leak) in CircuitPython that manifests
    # after a sequence of ConnectionError exceptions thrown from withing the wifi module.
    # Should not happen given the above 'except ConnectionError',
    # however adding that here just in case.
    hard_reset(e)
except Exception as e:  # pylint: disable=broad-except
    # This assumes that such exceptions are quite rare.
    # Otherwise, this would drain the battery quickly by restarting
    # over and over in a quick succession.
    watchdog.mode = None
    print("Code stopped by unhandled exception:")
    print(traceback.format_exception(None, e, e.__traceback__))
    RELOAD_TIME = 3
    print(f"Performing a supervisor reload in {RELOAD_TIME} seconds")
    time.sleep(RELOAD_TIME)
    supervisor.reload()
except WatchDogTimeout as e:
    hard_reset(e)

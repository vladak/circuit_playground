"""
Use the VCNL4020 proximity reading above certain threshold as a way to turn
the QtPy Neopixel on/off, basically simulating a switch.
"""

import time
import board
import busio
import adafruit_vcnl4020
import neopixel

from adafruit_ticks import ticks_ms, ticks_diff

from binarystate import BinaryState


PROXIMITY_THRESHOLD = 3000
DURATION_THRESHOLD_MS = 500        # duration in miliseconds

def led_on(pixel, color=(0, 0, 255), brightness=0.3):
    """
    Switch the Neopixel on with specified color.
    """
    pixel.fill(color)
    pixel.brightness = brightness


def led_off(pixel):
    """
    Switch the Neopixel on
    """
    pixel.brightness = 0


def led_is_on(pixel):
    """
    return if the Neopixel is on
    """
    return pixel.brightness > 0


def main():
    try:
        i2c = board.I2C()
    except RuntimeError:
        # QtPy
        i2c = busio.I2C(board.SCL1, board.SDA1)

    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
    led_off(pixel)
    sensor = adafruit_vcnl4020.Adafruit_VCNL4020(i2c)

    # Tuning experiments:
    # print(f"LED current: {sensor.led_current}")
    # sensor.low_threshold = (3000,)
    # sensor.low_threshold_interrupt = True
    # sensor.led_current = 500

    proximity_state = BinaryState()

    flipped = False

    while True:
        proximity = sensor.proximity
        # print(f"High threshold: {sensor.high_threshold}")
        # print(f"Low threshold: {sensor.low_threshold}")

        if proximity > PROXIMITY_THRESHOLD:
            state = "up"
        else:
            state = "down"

        print(f"Proximity is: {proximity} ({state})")

        duration = proximity_state.update(state)
        print(f"Duration of {state}: {duration} ms")
        if state == "up" and not flipped and duration > DURATION_THRESHOLD_MS:
            flipped = True
            if led_is_on(pixel):
                led_off(pixel)
            else:
                led_on(pixel)

        if state == "down":
            flipped = False

        time.sleep(0.1)


if __name__ == "__main__":
    main()

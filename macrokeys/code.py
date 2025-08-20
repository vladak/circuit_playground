"""
code for the macro neokey keyboard

expects QtPy RP2040 with the 1x4 Neokey (https://www.adafruit.com/product/4980)
connected via STEMMA QT.
"""

import time
import board
import busio
from adafruit_neokey.neokey1x4 import NeoKey1x4
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# use STEMMA I2C bus on RP2040 QT Py
i2c_bus = busio.I2C(board.SCL1, board.SDA1)

neokey = NeoKey1x4(i2c_bus, addr=0x30)
keyboard = Keyboard(usb_hid.devices)

# states for key presses
key_states = [False, False, False, False]


def map_key(key):
    """
    map character to USB HID Keycode constant
    """
    if key.isalpha():
        return getattr(Keycode, key.upper())
    if key == " ":
        return Keycode.SPACE
    if key in (";", ":"):
        return Keycode.SEMICOLON
    if key == "=":
        return Keycode.EQUALS

    raise ValueError(f"unsupported key: '{key}'")


def get_keys(vals):
    """
    convert string to list of USB HID Keycode constants
    """
    return [map_key(key) for key in vals]


# pylint: disable=too-few-public-methods
class KeyAction:
    """
    storage class representing key action

    Technically, it could be passed a keyboard object to the __init__
    function and have a send() function that would send the key presses,
    however it would make long lines if used in list of KeyAction objects.
    """

    def __init__(self, atonce, vals):
        """
        If the 'atonce' argument is set to True all the values in 'vals'
        should be sent at once which is handy e.g. for modifier keys.
        """
        if isinstance(vals, list):
            self.vals = vals
        else:
            self.vals = [vals]

        self.atonce = atonce


# switch action definitons
switches = [
    (
        [
            KeyAction(True, [Keycode.SHIFT, map_key(":")]),
            KeyAction(False, get_keys("set paste")),
            KeyAction(False, Keycode.ENTER),
            KeyAction(True, [Keycode.SHIFT, map_key(":")]),
            KeyAction(False, get_keys("set mouse=")),
            KeyAction(True, [Keycode.SHIFT, Keycode.QUOTE]),
            KeyAction(False, get_keys("off")),
            KeyAction(True, [Keycode.SHIFT, Keycode.QUOTE]),
            KeyAction(False, [Keycode.ENTER]),
        ],
        0xFF0000,
    ),
    ([], 0xFFFF00),
    ([KeyAction(True, [Keycode.CONTROL, map_key("w")])], 0x00FF00),
    ([KeyAction(True, [Keycode.CONTROL, map_key("x")])], 0x00FFFF),
]

while True:
    # switch debouncing (TODO: use the debouncer library ?)
    #  also turns off NeoPixel on release
    for i, _ in enumerate(key_states):
        if not neokey[i] and key_states[i]:
            key_states[i] = False
            neokey.pixels[i] = 0x0

    #
    # It would be nice to be able to call keyboard.send(*vals)
    # however that attempts to send all the values at once results in
    # arbitrary key ordering.
    #
    for i, _ in enumerate(key_states):
        if neokey[i] and not key_states[i]:
            neokey.pixels[i] = switches[i][1]
            for action in switches[i][0]:
                if action.atonce:
                    keyboard.send(*action.vals)
                else:
                    for val in action.vals:
                        keyboard.send(val)
                        time.sleep(0.01)
            key_states[i] = True

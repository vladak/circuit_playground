
# Purpose

To complement my portable keyboard with a set of macro keys, predefined
with shortcuts for ViM, screen etc. I used the
[NeoKey Emoji Keyboard guide](https://learn.adafruit.com/neokey-emoji-keyboard)
and changed the code to emit sequences of characters instead of emojis.

# Links

- [NeoKey Emoji Keyboard guide](https://learn.adafruit.com/neokey-emoji-keyboard)
- [QtPy RP2040](https://www.adafruit.com/product/4900)
- [NeoKey 1x4 QT I2C](https://www.adafruit.com/product/4980)
- Keycode constants: https://github.com/adafruit/Adafruit_CircuitPython_HID/blob/main/adafruit_hid/keycode.py

# Caveats/limitations

w.r.t. the printing/model/build:
  - the snap fit does not really snap so the QtPy floats around. there should be
    some supporting structure on inside of the top lid to hold the QtPy in
    place.
  - the heads of the screws sticking out on the bottom makes this pretty wobbly,
    esp. when pressing the key located at the end. it would be nicer if there
    were cavities for the screws to hide the screw heads.

"""
rolling text on multisegment LED display
"""

import adafruit_ht16k33.segments

import board
import sys

i2c = board.I2C()

display = adafruit_ht16k33.segments.Seg14x4(i2c)

display.fill(0)
display.show()

import time

def get_rolling_slice(text : str, idx : int, length : int):
    """
    Assumes len(text) >= len
    :param text: input text
    :param idx: index to get the slice at
    :param length: length of the slice
    :return: slice of the text of given length potentially rolled to the beginning
    """
    assert len(text) >= length

    if idx + length <= len(text):
        return text[idx : idx + length]
    else:
        # print(f"{idx}")
        return text[idx :] + text[:(length - (len(text) - idx))]

text = "green and vegetables for the best price".upper()
text += " "
# TODO: pad the text to length if shorter
while True:
    for i in range(0, len(text)):
        text_slice = get_rolling_slice(text, i, 4)
        display.print(text_slice)
        display.show()
        time.sleep(0.3)



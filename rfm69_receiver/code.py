"""
Receive packets over radio using RFM69 in Europe.
"""

import board
import busio
import digitalio

import adafruit_rfm69


# Assumes certain witing of the Radio FeatherWing.
CS = digitalio.DigitalInOut(board.D14)
RESET = digitalio.DigitalInOut(board.D32)

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, 433)  # Europe

# Print out some chip state:
print("Temperature: {0}C".format(rfm69.temperature))
print("Frequency: {0}mhz".format(rfm69.frequency_mhz))
print("Bit rate: {0}kbit/s".format(rfm69.bitrate / 1000))
print("Frequency deviation: {0}hz".format(rfm69.frequency_deviation))

# Wait to receive packets.  Note that this library can't receive data at a fast
# rate, in fact it can only receive and process one 60 byte packet at a time.
# This means you should only use this for low bandwidth scenarios, like sending
# and receiving a single message at a time.
print("Waiting for packets...")
while True:
    packet = rfm69.receive(timeout=0.5)
    if packet is None:
        print("Received nothing! Listening again...")
    else:
        print("Received (raw bytes): {0}".format(packet))
        # TODO: print bytes that are ASCII printable, other in hex

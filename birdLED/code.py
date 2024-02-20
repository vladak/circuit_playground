import os
import time
import adafruit_logging as logging
import ipaddress
import supervisor
import board
import wifi
import ssl
import socketpool
import neopixel
from rainbowio import colorwheel
import busio
import adafruit_veml7700
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import json

from secrets import secrets

SLEEP_COLOR = (255, 0, 0)  # Red
WAKE_COLOR = (0, 0, 255)  # Blue

# TODO: configurable
# Canary brightness customisation.
# Brightness must be a float or integer between 0.0 and 1.0, where 0.0 is off, and 1.0 is max.
# This is the brightness of the canary during sleep time. It defaults to 0.2, or "20%".
# Increase or decrease this value to change the brightness.
LOW_BRIGHTNESS = 0.2
# This is the brightness of the canary during wake time. It defaults to 0.7, or "70%".
# Increase or decrease this value to change the brightness.
HIGH_BRIGHTNESS = 0.9


def blink(color, brightness):
    """
    Blink the NeoPixel LEDs a specific color.

    :param tuple color: The color the LEDs will blink.
    """
    pixels.brightness = brightness
    pixels.fill(color)
    time.sleep(0.5)
    pixels.fill((0, 0, 0))
    time.sleep(0.5)


def main():
    logger = logging.getLogger(__name__)
    # TODO: make the log level configurable
    logger.setLevel(logging.DEBUG)

    logger.info(f"Connecting to wifi {secrets['SSID']}")
    wifi.radio.connect(secrets["SSID"], secrets["password"], timeout=10)
    logger.info(f"Connected to {secrets['SSID']}")
    logger.debug(f"IP: {wifi.radio.ipv4_address}")

    # Assumes Adafruit 5x5 NeoPixel Grid BFF
    pixels = neopixel.NeoPixel(board.A3, 5*5,
                               brightness=LOW_BRIGHTNESS,
                               auto_write=False)

    i2c = board.STEMMA_I2C()
    veml7700 = adafruit_veml7700.VEML7700(i2c)

    pool = socketpool.SocketPool(wifi.radio)

    # TODO: make this configurable
    host = "172.40.0.3"
    port = 1883
    mqtt_client = MQTT.MQTT(
        broker=host,
        port=port,
        socket_pool=pool,
        ssl_context=ssl.create_default_context(),
        recv_timeout=5,
        socket_timeout=0.01,
    )

    mqtt_client.connect()

    pixels.fill(0)
    pixels.show()
    colors = [0, 0]
    hue = 0
    while True:
        #
        # Black the pixels for a bit so that reliable light reading
        # can be acquired (without the light coming from the Neopixel BFF).
        #
        pixels.fill(0)
        pixels.show()
        # The sleep seems to be needed to get good reading.
        time.sleep(0.2)
        light = veml7700.light
        lux = veml7700.lux
        logger.debug(f"Ambient light: {light}")
        logger.debug(f"Lux: {lux}")
        # TODO: make the topic configurable
        mqtt_client.publish("devices/koupelna/qtpy",
            json.dumps({"light": light, "lux": lux}))

        # TODO: map this configuously
        LIGHT_MIN = 50
        LIGHT_MAX = 800
        if light < 50:
            brightness = HIGH_BRIGHTNESS
        else:
            brightness = LOW_BRIGHTNESS

        logger.debug(f"brightness -> {brightness}")
        pixels.brightness = brightness

        # To handle MQTT ping.
        mqtt_client.loop(0.01)

        # TODO: fluctuate the brightness (within given boundary)
        for i in range(10):
            # Use a rainbow of colors, shifting each column of pixels
            hue = hue + 7
            if hue >= 256:
                hue = hue - 256

            colors[1] = colorwheel(hue)
            # Scoot the old text left by 1 pixel
            pixels[0:20] = pixels[5:25]

            # Draw in the next line of text
            for y in range(5):
                # Select black or color depending on the bitmap pixel
                pixels[20+y] = colors[1]
            pixels.show()
            time.sleep(.1)



if __name__ == "__main__":
    #
    # Rather than catch all possible exceptions and react, simply
    # set the supervisor to reload the program.
    #
    supervisor.set_next_code_file("code.py", reload_on_error=True)

    main()


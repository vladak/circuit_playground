"""
Remix of https://learn.adafruit.com/canary-nightlight

Instead of making the LED light based on time, use the VEML7700 light sensor.
Publish the data contiguously to MQTT topic.
"""

import json
import ssl
import time
import traceback
from secrets import secrets

import adafruit_logging as logging
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_veml7700
import board
import microcontroller
import neopixel
import socketpool
import supervisor
import wifi
from rainbowio import colorwheel

SLEEP_COLOR = (255, 0, 0)  # Red
WAKE_COLOR = (0, 0, 255)  # Blue

LIGHT_MIN = 50
LIGHT_MAX = 800

# TODO: configurable via secrets
# Brightness must be a float or integer between 0.0 and 1.0, where 0.0 is off, and 1.0 is max.
# This is the lowest brightness. It defaults to 0.2, or "20%".
MIN_BRIGHTNESS = 0.2
# This is the highest brightness to use. It defaults to 0.9, or "90%".
# At this level the Neopixel BFF can get pretty hot.
# TODO: monitor the temperature and scale down if too hot
MAX_BRIGHTNESS = 0.9


def blink(pixels, color, brightness):
    """
    Blink the NeoPixel LEDs a specific color.

    :param tuple color: The color the LEDs will blink.
    """
    pixels.brightness = brightness
    pixels.fill(color)
    time.sleep(0.5)
    pixels.fill((0, 0, 0))
    time.sleep(0.5)
    pixels.show()


# simple inverted range mapper, like Arduino map()
def map_range_cap_inv(s, a1, a2, b1, b2):
    """
    constrain the s value into a1,a2 range first, then map it to the range b1,b2 inverted
    based on https://learn.adafruit.com/todbot-circuitpython-tricks/more-esoteric-tasks
    """
    s = max(s, a1)
    s = min(s, a2)
    return b2 - ((s - a1) * (b2 - b1) / (a2 - a1))


def main():
    """
    main loop
    """
    logger = logging.getLogger(__name__)
    # TODO: make the log level configurable
    logger.setLevel(logging.DEBUG)

    logger.info(f"Connecting to wifi {secrets['SSID']}")
    wifi.radio.connect(secrets["SSID"], secrets["password"], timeout=10)
    logger.info(f"Connected to {secrets['SSID']}")
    logger.debug(f"IP: {wifi.radio.ipv4_address}")

    # Assumes Adafruit 5x5 NeoPixel Grid BFF
    pixels = neopixel.NeoPixel(
        board.A3, 5 * 5, brightness=MIN_BRIGHTNESS, auto_write=False
    )

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
    publish_stamp = 0
    while True:
        #
        # Acquire light metrics and publish them. Do this only once a second or so
        # not to spam the MQTT topic too much.
        #
        # TODO: refactor
        if publish_stamp < time.monotonic_ns() // 1_000_000_000 - 1:
            light = veml7700.light
            lux = veml7700.lux
            logger.debug(f"Ambient light: {light}")
            logger.debug(f"Lux: {lux}")
            publish_stamp = time.monotonic_ns() // 1_000_000_000

            # TODO: make the topic configurable
            try:
                mqtt_client.publish(
                    "devices/koupelna/qtpy", json.dumps({"light": light, "lux": lux})
                )
            except (OSError, MQTT.MMQTTException) as pub_exc:
                logger.error(f"failed to publish: {pub_exc}")
                # If the reconnect fails with another exception, it is time to reload
                # via the generic exception handling code around main().
                mqtt_client.reconnect()

            # Map the light value contiguously into the brightness range.
            brightness = map_range_cap_inv(
                light, LIGHT_MIN, LIGHT_MAX, MIN_BRIGHTNESS, MAX_BRIGHTNESS
            )
            logger.debug(f"brightness -> {brightness}")
            pixels.brightness = brightness

        # TODO: fluctuate the brightness (within given boundary)
        for _ in range(10):
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
                pixels[20 + y] = colors[1]
            pixels.show()
            time.sleep(0.1)

        # To handle MQTT ping. Also used not to loop too quickly.
        try:
            mqtt_client.loop(0.1)
        except (OSError, MQTT.MMQTTException) as loop_exc:
            logger.error(f"failed to publish: {loop_exc}")
            # If the reconnect fails with another exception, it is time to reload
            # via the generic exception handling code around main().
            mqtt_client.reconnect()


try:
    main()
except ConnectionError as e:
    # When this happens, it usually means that the microcontroller's wifi/networking is botched.
    # The only way to recover is to perform hard reset.
    print("Performing hard reset")
    microcontroller.reset()  # pylint: disable=no-member
except MemoryError as e:
    # This is usually the case of delayed exception from the 'import wifi' statement,
    # possibly caused by a bug (resource leak) in CircuitPython that manifests
    # after a sequence of ConnectionError exceptions thrown from withing the wifi module.
    # Should not happen given the above 'except ConnectionError',
    # however adding that here just in case.
    print("Performing hard reset")
    microcontroller.reset()  # pylint: disable=no-member
except Exception as e:  # pylint: disable=broad-except
    # This assumes that such exceptions are quite rare.
    # Otherwise, this would drain the battery quickly by restarting
    # over and over in a quick succession.
    print("Code stopped by unhandled exception:")
    print(traceback.format_exception(None, e, e.__traceback__))
    print("Performing code reload")
    supervisor.reload()

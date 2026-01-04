"""
Remix of https://learn.adafruit.com/canary-nightlight

Instead of making the LED light based on time, use the VEML7700 light sensor.
Publish the data contiguously to MQTT topic.
"""

import json
import ssl
import time
import traceback

import adafruit_logging as logging
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_veml7700
import board
import microcontroller
import neopixel

# pylint: disable=import-error
import socketpool

# pylint: disable=import-error
import supervisor

# pylint: disable=import-error
import wifi

from logutil import get_log_level

try:
    from secrets import secrets
except ImportError:
    print(
        "WiFi credentials and configuration are kept in secrets.py, please add them there!"
    )
    raise


# tunables
BROKER_PORT = "broker_port"
MQTT_TOPIC = "mqtt_topic"
BROKER = "broker"
PASSWORD = "password"
SSID = "ssid"
LOG_LEVEL = "log_level"
BRIGHTNESS_RANGE = "brightness_range"
LIGHT_RANGE = "light_range"
HOURS_RANGE = "hours_range"


class SecretsException(Exception):
    """
    Raised on missing or invalid configuration item.
    """


def bail(message):
    """
    Raise distinct exception to handle on the top level.
    """
    raise SecretsException(message)


def check_string(name, mandatory=True):
    """
    Check is string with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, str):
        bail(f"not a string value for {name}: {value}")


def check_int(name, mandatory=True):
    """
    Check is integer with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, int):
        bail(f"not a integer value for {name}: {value}")


def check_tuple(name, mandatory=True, numitems=2):
    """
    Check is tuple with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, tuple):
        bail(f"not a integer value for {name}: {value}")

    if len(value) != numitems:
        bail(f"tuple must have {numitems} items: {value}")


def check_mandatory_tunables():
    """
    Check that mandatory tunables are present and of correct type.
    Will exit the program on error.
    """
    check_string(LOG_LEVEL)
    check_string(SSID)
    check_string(PASSWORD)
    check_string(BROKER)
    check_string(MQTT_TOPIC)

    check_int(BROKER_PORT)

    check_tuple(BRIGHTNESS_RANGE)
    check_tuple(LIGHT_RANGE)
    check_tuple(HOURS_RANGE)

    # Brightness must be a float or integer between 0.0 and 1.0, where 0.0 is off, and 1.0 is max.
    for value in secrets.get(BRIGHTNESS_RANGE):
        if value is None:
            bail(f"{BRIGHTNESS_RANGE} value is None")
        if not isinstance(value, float):
            bail(f"{value} must be float")
        if value > 1:
            bail(f"{value} must be smaller than 1")

    for value in secrets.get(LIGHT_RANGE):
        if value is None:
            bail(f"{LIGHT_RANGE} value is None")
        if not isinstance(value, int):
            bail(f"{value} must be int")
        if value < 0:
            bail(f"{value} must be positive integer")

    for value in secrets.get(HOURS_RANGE):
        if value is None:
            bail(f"{HOURS_RANGE} value is None")
        if not isinstance(value, int):
            bail(f"{value} must be int")
        if value < 0 or value > 24:
            bail(f"{value} must be positive integer and less than 24")


# simple inverted range mapper, like Arduino map() but inverted
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
    check_mandatory_tunables()

    log_level = get_log_level(secrets[LOG_LEVEL])
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    logger.info("Running")

    logger.info(f"Connecting to wifi {secrets[SSID]}")
    wifi.radio.connect(secrets[SSID], secrets[PASSWORD], timeout=10)
    logger.info(f"Connected to {secrets[SSID]}")
    logger.debug(f"IP: {wifi.radio.ipv4_address}")

    # Assumes Adafruit 5x5 NeoPixel Grid BFF
    pixels = neopixel.NeoPixel(
        board.A3, 5 * 5, brightness=secrets.get(BRIGHTNESS_RANGE)[0], auto_write=False
    )

    # pylint: disable=no-member
    i2c = board.STEMMA_I2C()
    veml7700 = adafruit_veml7700.VEML7700(i2c)
    # TODO: tune the sensitivity of the light sensor

    pool = socketpool.SocketPool(wifi.radio)

    mqtt_client = MQTT.MQTT(
        broker=secrets[BROKER],
        port=secrets[BROKER_PORT],
        socket_pool=pool,
        ssl_context=ssl.create_default_context(),
        recv_timeout=5,
        socket_timeout=0.01,
    )

    logger.info("Connecting to MQTT broker")
    mqtt_client.connect()

    # initialize the pixels with given color and 0 brightness
    pixels.fill((255, 100, 0))  # TODO: make this tunable
    pixels.show()
    publish_stamp = 0
    while True:
        brightness_max, light, lux = get_brightness(veml7700)

        data = {
            "light": light,
            "lux": lux,
            "brightness_max": brightness_max,
            # pylint: disable=no-member
            "cpu_temp": microcontroller.cpu.temperature,
        }
        publish_stamp = publish_data(mqtt_client, publish_stamp, data)

        display_pixels(pixels, brightness_max)

        # To handle MQTT ping. Also used not to loop too quickly.
        try:
            mqtt_client.loop(0.01)
        except (OSError, MQTT.MMQTTException) as loop_exc:
            logger.error(f"failed to publish: {loop_exc}")
            # If the reconnect fails with another exception, it is time to reload
            # via the generic exception handling code around main().
            mqtt_client.reconnect()


# pylint: disable=too-many-arguments
def publish_data(mqtt_client, publish_stamp, data):
    """
    Publish metrics to MQTT topic.

    Do this only once in a while in order not to spam the MQTT topic too much.

    Return the time of publish (which may be the original time passed in).
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"publish stamp: {publish_stamp}")
    # TODO: use adafruit time diff library
    if (
        publish_stamp < time.monotonic_ns() // 1_000_000_000 - 10
    ):  # TODO: make this configurable
        # TODO: monitor the temperature and scale the brightness down if too hot
        try:
            mqtt_client.publish(
                secrets[MQTT_TOPIC],
                json.dumps(data),
            )
            publish_stamp = time.monotonic_ns() // 1_000_000_000
        except (OSError, MQTT.MMQTTException) as pub_exc:
            logger.error(f"failed to publish: {pub_exc}")
            # If the reconnect fails with another exception, it is time to reload
            # via the generic exception handling code around main().
            mqtt_client.reconnect()

    return publish_stamp


def display_pixels(pixels, brightness_max, brightness_min=0.1):
    """
    Change pixels in a complete round of iterations for given brightness level.

    The minimal brightness level is stricly greater than zero otherwise this
    would create unwelcome effect of darkness blip in between the function call.
    """
    logger = logging.getLogger(__name__)

    sleep_duration = 0.1
    brightness = brightness_min

    logger.debug("brightness cycle start")
    while brightness <= brightness_max:
        pixels.brightness = brightness
        pixels.show()
        time.sleep(sleep_duration)
        brightness += 0.01
    brightness = brightness_max
    while brightness >= brightness_min:
        pixels.brightness = brightness
        pixels.show()
        time.sleep(sleep_duration)
        brightness -= 0.01
    logger.debug("brightness cycle end")


def get_brightness(veml7700):
    """
    Get maximum brightness based on current light level.
    """
    logger = logging.getLogger(__name__)

    light = veml7700.light
    lux = veml7700.lux
    logger.debug(f"Ambient light: {light}")
    logger.debug(f"Lux: {lux}")

    # Map the light value contiguously into the brightness range.
    brightness = map_range_cap_inv(
        light,
        secrets.get(LIGHT_RANGE)[0],
        secrets.get(LIGHT_RANGE)[1],
        secrets.get(BRIGHTNESS_RANGE)[0],
        secrets.get(BRIGHTNESS_RANGE)[1],
    )

    logger.debug(f"brightness = {brightness}")
    return brightness, light, lux


try:
    main()
except SecretsException as e:
    print(f"secrets error: {e}")
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

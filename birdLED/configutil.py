"""
functions for handling configuration
"""

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

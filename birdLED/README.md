# BirdLED

Remix of https://learn.adafruit.com/canary-nightlight. In addition to using time for controlling the light emitted by the LED array, 
the [VEML7700 light sensor](https://www.adafruit.com/product/5378) is used.
The less light there is, the higher brightness is used for the Neopixels.

MQTT is used for publishing the light sensor data for calibration.

## Hardware setup

Use long STEMMA cable for connecting the light sensor so that it is less impacted by the light emitted from the LED array.

TBD

## Configuration

The `secrets.py` can look e.g. like this:
```python
secrets = {
    "ssid": "XXX",
    "password": "XXX",
    "broker": "172.40.0.3",
    "broker_port": 1883,
    "mqtt_topic": "devices/koupelna/qtpy",
    "log_level": "debug",
    # The max brightness is the highest brightness to use. It defaults to 0.9, or "90%".
    # At this level the Neopixel BFF can get pretty hot.
    "brightness_range": (0.1, 0.9),
    # max light value should correspond to a state when **some** light is on
    "light_range": (10, 50),
    "light_gain": 2,
    "hours_range": (9, 18),
}
```

`light_gain` sets the VEML7700 sensor light sensitivity and is optional.
Can be either `1` or `2` if set. The `light_range` needs to be set accordingly.

## Install

1. Use `circup` to install the pre-requisites:
```
circup install -r requirements.txt
```
2. Create `secrets.py`
3. copy `*.py` files over

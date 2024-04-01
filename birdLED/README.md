# BirdLED

Remix of https://learn.adafruit.com/canary-nightlight. In addition to using time for controlling the light emitted by the LED array, 
the intention is to use the [VEML7700 light sensor](https://www.adafruit.com/product/5378).
The less light there is, the higher brightness is used for the Neopixels.

MQTT is used for publishing the light sensor data for calibration.

## Hardware setup

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
    # max light value should correspond to a state when the **some** light is on
    "light_range": (10, 50),
    "hours_range": (9, 18),
}
```

## Install

1. Use `circup` to install the pre-requisites:
```
circup install -r requirements.txt
```
2. Create `secrets.py`
3. copy `*.py` files over

# BirdLED

Remix of https://learn.adafruit.com/canary-nightlight. Instead of using time for controlling the light, 
the intention is to use the [VEML7700 light sensor](https://www.adafruit.com/product/5378).
The less light there is, the higher brightness is used for the Neopixels.

MQTT is used for publishing the light sensor data.

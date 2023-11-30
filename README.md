# softub-wifi
A project for a wifi adapter for a Softub that sits between the top unit and temperature probe, and the stock Softub control board.

It is based on the reverse engineering figured out by Monroe Wiliams.  See:
https://github.com/monroewilliams/softub/blob/master/hardware/reverse-engineering.md

This is based on a custom circuit board, using a Seed XIAO ESP32S3.

I'm using this with Home Assistant  (integration with homeassistant is done with MQTT.  (See mqtt.py)

TODO:
The temperature probe on a hot tub isn't in the best location, so its hard to use the probe to come up with the actual temperature.

The stock controller (from 20 years ago), seemed to turn on when it was 2 degrees below the set point and off when it reached the set point.  Once I get more data I'm hoping to more accurately estimate the temperature.  For now it just reports the temperature of the probe.

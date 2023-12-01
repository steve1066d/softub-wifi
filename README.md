# softub-wifi
A project for a wifi adapter for a Softub that sits between the top unit and temperature probe, and the stock Softub control board.

This is meant to be used with a circuit board which can be ordered here:
https://oshpark.com/shared_projects/QC1GjVG6

It is based on the reverse engineering figured out by Monroe Wiliams.  See:
https://github.com/monroewilliams/softub/blob/master/hardware/reverse-engineering.md

### It has the following features:
* It provides WiFi support to display or modify temperature.
* It works with the existing controller board. The safety high temp cutoff is not bypassed, so it continues works for safety.
* It supports increasing the set-points in half degree increments using the up and down buttons.
* Holding down the buttons for over a second will cause the temp change to continue to repeat.
* It can display temps in either Celsius or Farenheight
* It can go to 106F (or whatever max temperature you like) without any special modes.
* Even on older boards that don't show the current temp, this will still display the current temp.
* It will still display the setting temperature for a few seconds after changing, either through WiFi or the buttons.
* It can optionally display temperatures in tenth of a degrees.  (Over 100 degrees would not show the "1")
* It can integrate with Home Assistant using MQTT.  It appears as a thermostat, and can be controlled with Alexa, if configured.
* It can report button presses back to MQTT.  So for instance you could configure Home Assistant to turn off lights if the Softub lights button is pressed.

### It does this by:
* It uses a custom circuit board with a Seed XIAO ESP32S3 that plugs into the controller board where the display and temperature sensor currently plug into.  (Then then display and temperature sensor plug into this circuit board.
* It uses Adafruit 16 bit ADC and DAC boards to perform high accuracy temperature reads and reporiting.  (It is probably overkill, as the ESP32 has analog in and out, but the boards weren't very expensive).
* It communicates with both the board and display, and working with either the softub buttons or Wifi
* It adjusts the temperature reported to the stock Softub board as appropriate.  So if you set the temp at 102.5, it will keep the board at 102, but decrease the temp sent to the board by 1/2 degree. Or if you select over 104, it decreases the reported temp by the amount over 104.

### Work left to do:
* Improve the detection of when the tub is actually running. Because the panel doesn't show when the tub is running, I'm currently using a response from Home Assistant to return the state.  However, it should work to use the combination of the Heat and filter indicators, and when the Jets button was last pressed to do the same thing.  Another option would be to find a spot on the board to return the motor state that I could tie into.
* The temperature probe on a hot tub isn't in the best location, so its hard to use the probe to come up with the actual temperature.
* Allow temporarily turning off the pump by pressing the Jets button even when it is calling for heat.  This might be able to be done by temporarily raising the reported temperature.

The stock controller (from 20 years ago), seemed to turn on when it was 2 degrees below the set point and off when it reached the set point. But because the probe is in the pump and not in the tub, it doesn't really reflect the real temperatures. Once I get more data I'm hoping to more accurately estimate the temperature.  For now it just reports the temperature of the probe.

### Possible Improvements
* Create a version of the PCB and software that replaces the existing board. Ideally it would have the same tabs and connections so it would be a simple replacement, not requiring any soldering or new crimping.  My thoughts are to saftety cut off configured in hardware to shut the tub off with a simple circuit, so the safety of the original design remains.
* Allow replacing the existing temperature probes with other easier to obtain probes.  For example, using $10 1-wire digital probe could work just as well, as the expensive replacement official probes.
  

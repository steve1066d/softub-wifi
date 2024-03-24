# Softub Replacement Firmware

I'm working on a replacement firmware that can be installed on a Softub board by replacing the microcontroller.

## Features

This replacement firmware for the Softub works similar to the Softub provided
one, with a few enhancements.  Note that this product is not affiliated with 
Softub.  Softub and HydroMate are registered trademarks of Softub, Inc.

The following are the differences and enhancements of the this firmware over 
the stock firmware provided by Softub.

When power is first provided, the tub will show its set point for 5 seconds,
and then show the standard "P" (or the tub temperature if so configured).

To quickly move the set temperature up or down hold down the button for 2 
seconds, and it will start repeating.  Lift up when the desired set temperature
is reached.

If a tub is running and the jets button is pressed, the tub will stop for 20 
minutes, even if it is heating  (The stock program only will stop if it isn't 
heating. After the 20 minutes, it will start again, if it cool enough to call
for heat.  However, if the ozone generator is running, the jets button will 
first stop the ozone, so if that is the case, and you want to stop the jets,
press the jets button a second time.

The special programs (SP1, Economy and Overnight nodes), can be chosen by
holding down the buttons for 4 seconds instead of 9 seconds the stock one
requires.  Also, you can enter SP1 without first setting the temperature to 104.  
The Economy and Overnight modes work fine even if the tub isn't up to 
temperature when they are set. When the Economy is exited (by holding down the
down and light buttons), The "24" will blink twice to indicate it is turned off.
Likewise holding down the down, light, and jets button will turn off the 
overnight mode, blinking "12" twice.

Once a temperature or special mode is selected, it will keep the setting even
if the tub loses power. So if the tub is set to 102, instead of returning back
to 100, it will retain the temperature of 102. However, because the board 
doesn't keep time when it is off, it may run at odd times if the overnight or 
economy mode is selected when power is lost. If that happens, reselect the 
special mode or restart the tub at the right time.

Holding the up and down buttons together for 4 seconds will disable the "P" mode, 
increase the maximum temperature allowed to be set by 2 degrees F (1 degree C). 
This is provided as a simpler way to get to get to the higher temperatures, and
to allow the user to see the temperature of the tub, even if it is off.  Holding
down the up and down buttons a second time will change the tub back to using P,
and will decrease the maximum temperature by 2 degrees.
 
If P mode is disabled, the tub will show the temperature even when not running. 
The temperature it shows will likely be lower that the actual temperature, since
the probe is in the HydroMate and not the tub.

## Service Mode

It is possible to go into a special service mode to change various settings
of this firmware. Please be sure you understand the ramifications of these
settings before changing anything.  It is not expected that the user of the 
tub will be modifying these setting.  They are for service personnel for their
specific needs.

To enter the service mode, press all 4 buttons for 4 seconds. You should see
PP0 on the display.  If you have issues with the system not recognizing 4 
buttons, hold down the lights button, then press each of the other buttons.  
After you have pressed the last button, the service mode should start after 4 
seconds.  Then release the lights button.

Use the up and down arrows to choose the setting you wish to set.  Use the 
Lights button to select the value to change. Pressing jets will save the 
settings return to the normal controls.

After pressing the lights button, it will show the current setting.  Use the 
lights button to move to the next digit.  The digit you are at will flash.  If 
the hundreds place is selected and has a 0 it will not flash because the 
display cannot show a 0 in that position. To save the value, press 
the jets button. If you don't respond within 5 seconds, the system
will go back to the previous menu without saving any changes.

Valid values are between 0 and 255. There's no error checking so 
be careful what you set things to and verify the settings do what you are
expecting. If you want to revert to default settings, set the default 
temperature (PP0) to "255".  On next restart it will replace all settings with
defaults.

While in the service mode you can press the up and down  buttons to reset the 
Softub. Doing so will not save any changes you have made.

#### PP0: Default temperature.  
If you want the system to be set to a different temperature on startup, change 
this.  Though normally this is changed automatically when the setting changes.

#### PP1:
Probe offset. This is tenths of a degree (or 20th of a degree in C) to offset 
the probe setting, with 10.0  as the base. So a setting of "9.0" will cause the 
temperature to be reported 1 degree colder.  A setting of 12.0 will be 2 
degrees warmer.  Values under 10.0 cause pool temps to get hotter because it is 
adjusted to a lower temperature.

#### PP2 Minimum temp allowed.  
The minimum temperature allowed to be set.  Make sure it is safely above 
freezing.

#### PP3 Maximum allowed temp.  
The maximum allowed temp.  The default 104F (80C) is the recommended maximum 
temperature for hot tubs. This adjustment is provided if you want to lower the 
maximum if you have children, or are otherwise concerned about the maximum 
temperature. Increasing this is not recommended for safety reasons. Also, 
setting this too high will cause the board's high limit safety feature to 
activate, disabling the pump.

#### PP4 Pump on value
Once the tub is up to temp, the system waits until the temp probe goes down 
this many degrees F (or half degrees C) before calling for heat again. The 
default is 4 but if you increase it, the pump will run less often (but for 
longer).  As power cycles increase the wear on the pump, It may be helpful to 
adjust this.  It is important to note that the temp probe is inside the 
HydroMate, so you may find that a large deadband only causes a small fluctuation 
in tub temperature.

#### PP5 Pump off value
If the pump is heating, if the temperature is this degrees F over (or half 
degrees C), then the pump will shut off.  The default is 2.

#### PP6 Operational flags
To use this, add up the numbers and configure that value.  So if you want to 
use Fahrenheit, disable P and disable IPS, you would enter 11 (1 + 2 + 8).  
Note that generally the flags disable something, so you would set it to "1" to 
disable the feature.

1 = Use Fahrenheit.  If this is not set it will display the temperature in
half degreees Celsius. The default is the setting of JP2 on the board.  If the
pad is jumpered the default is Celsius. If you change this flag, it will replace the 
maximum, minimum and default temps to default values.

2 = Disable P.  Normally the controller will use the stock rules of displaying P 
when the pump is off or just started.  If this flag is set, it will just report 
what the temp is in the HydroMate, which may not be all that accurate. Not that
it is all that accurate in the first place, as it really takes the pump running
for about an hour to display accurate readings.

4 = Disable Ozone.  Softub has an optional ozone generator that is run 
periodically to limit the chemical use.  However, they tend to fail, and 
generally are not replaced. If you are not using or do not wish to use the 
ozone generator, set this flag.

8 = Disable IPS.  The board monitors the voltage is sufficient to not 
cause damage to the pump. It fires if the voltage drops to 96.5 volts on a 120v
system (or probably around 177 v on a 220 circuit).  To disable this test, set 
this flag. However, if there is insufficient power for the microcontroller, 
it could still respond with an IPS warning.

16 = Disable P01:  If the tub has been heating for 4 hours without a 1 degree 
temperature increase, the system will stop, and display a P01 error.  If you 
would rather it keep going in those situations, set this flag.

32 = Disable SP1: 
The controller allows you to go up to 2 degrees F higher (or 1 degree C) than 
the maximum configured in PP1, by using the "special temperature" controls that 
the stock Softub board uses. If you wish to disable this for safety, or if you 
changed the maximum to where you want it in PP1, set this flag.

64 = Disable Temperature processing:
The software tries to estimate the tub temperature when it is off.  If instead
you want to display the raw temperature of the probe, use this flag. It only
affects measurements when the "P" mode would have hidden the temperature. It
also only affects the display value and doesn't affect the operation of the tub.
 
#### PP7  Additional service flags.
1 = Disable Save settings:
The controller will normally save the selected temperature and the mode the 
tub is running in so it will keep that setting if power is lost.  If you rather
it instead always return to the saved defaults, set this flag.

2 = Disable service menu.  This could be useful if you have the settings you want 
and you don't want anyone to muck with them.  If this is disabled, holding the 
four buttons simply causes the controller to restart. However, if you set this
flag, it means that you won't be able to change any of these PP settings without 
opening up the HydroMate. Temporarily adding a jumper across JP3 on the board on 
startup will reset the configuration to the default and reenable this menu.

4 = Disable wait for service menu.
If this is enabled, then pressing the 4 buttons will immediately bring up the
service menu instead of requiring a 4 second hold

8 = Disable Decimal
If this is enabled, then the board will not try to send out a decimal point.
Decimal points are only used for Celsius, and the PP01 menu. The early 2001 top
units (with a + and - instead of an up and down arrows) cannot display decimal
points).

#### PP8 Mode.  
This does not need to be edited, as it can be changed with the documented commands
00 = Startup in normal mode
01 = Startup in economy mode
02 = Startup in overnight mode


### Alternate Buttons

If a top panel button or buttons fail, it is possible to add a normally open 
push button to the the jumper pads on the board.  To do this you would need to
solder a pair of wires on the jumper pads, then route the wires for the 
pushbutton out of the enclosure.  If you go this route, make sure you have a 
waterproof cable nut to protect the enclosure from getting wet and you route the 
cable so that it it has a dip below the pump to make sure water doesn't work its 
way into the control panel box. It would be better to replace the control panel, 
but this is an option for someone confident on their installation skills.  You 
can either replace all the buttons or just the broken buttons.  Here's the 
connection placements:

JP3: Jets
JP4: Lights
JP5: Up
JP6: Down

### Sonoff Integration
There is a planned future integration with Sonoff Elite, which will allow wifi
operation and integration with digital assistants Alexa and Google Home. It will
report the tub temperature back to Sonoff, and allow Sonoff to control the Softub
while still allowing the tub's control panel to work normally.  This will be done
with a small adapter board that connects to J9.

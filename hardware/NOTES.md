### Notes on the hardware.

* The silkscreen indicated to use a Adafruit ESP32-S2 board, but that didn't work out because it only had 2 uarts. 3 are needed for the board, display, and USB interface.
Though a S2 board could work if you don't need to debug things, since it seems to work ok as long as it isn't connected with USB.
* To send the temperature back to the controller, there's a couple options.  If you have softub_controlled to False, you can use an ESP32-S2 with the DAC built in.  If you use_softub_controlled to be true, you need the DAC board.  It has similar pinouts to the ADC, so you can either stack the board on top of it, or use a cable to connect the DAC to the ADC.  You could also skip the ADC and just use the DAC, but the built in ADC is rather noisy, so you may find the temp jumps around more than you like.

* The USB jumper can be permanently jumped, as it would only be required if you wanted to use the USB while it was hooked up to the tub.  But as it turns out unless you have a right angle USB connector, there isn't room to plug a USB cable while the board is in place anyways.

Here's a link to a Digikey cart with all the parts:
https://www.digikey.com/short/1w793r53

To install firmware on the ESP32-S3, use these directions
https://wiki.seeedstudio.com/XIAO_ESP32S3_CircuitPython/

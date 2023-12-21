### Notes on the hardware.

* The silkscreen indicated to use a Adafruit ESP32-S2 board, but that didn't work out because it only had 2 uarts. 3 are needed for the board, display, and USB interface.
# Though a S2 board could work if you don't need to debug things, since it seems to work ok as long as it isn't connected with USB.
* However, one limitation with the ESP32-S3 board is that it doesn't support analog out. So I stacked a DAC board on the ADC board, as the pinouts were similar.
* The USB jumper can be permanently jumped, as it would only be required if you wanted to use the USB while it was hooked up to the tub.  But as it turns out unless you have a right angle USB connector, there isn't room to plug a USB cable while the board is in place anyways.

Here's a link to a Digikey cart with all the parts:
http://www.digikey.com/short/jmnhjvj4

To install firmware on the ESP32-S3, use these directions
https://wiki.seeedstudio.com/XIAO_ESP32S3_CircuitPython/

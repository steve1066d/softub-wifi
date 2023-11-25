import time
"""Tests the Softub controller"""
"""
This uses an Adafruit ESP32-S2 Feather, with an
Addafruit FeatherWing OLED - 128x64 OLED display_bus

Wiring:
MOSI  9  IO8
MISO 10  IO9
RX    8  IO44
TX    7  IO43
"""

import board
import microcontroller
import supervisor
from analogio import AnalogOut
from softub import Softub
from ticks import is_due, ticks_diff, ticks_add
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1107
from digitalio import DigitalInOut, Direction, Pull
from analogio import AnalogOut
from adafruit_simplemath import map_unconstrained_range

i2c = board.I2C()  # uses board.SCL and board.SDA
displayio.release_displays()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
_display = adafruit_displayio_sh1107.SH1107(
    display_bus, width=128, height=64, rotation=0
)
display_group = displayio.Group()
_display.show(display_group)
label = label.Label(terminalio.FONT, scale=2, text="Softub Tester", y=8)
display_group.append(label)
set_temp = 100
current_temp = 100
analog_out = AnalogOut(board.A1)
last_button = None

def set_temperature():
    adj_out = map_unconstrained_range(95, 95, 102, 102, current_temp)
    x = int(adj_out / 3.3 * 655.35)
    analog_out.value = x

def callback():
    global buttons, set_temp, last_button
    if last_button != softub.top_buttons:
        if softub.top_buttons & softub.button_up:
            print("up")
            set_temp += 1
        if softub.top_buttons & softub.button_down:
            set_temp -= 1
            print("down")
        softub.display_temperature(set_temp)
        last_button = softub.top_buttons
    softub.display_heat(current_temp < set_temp)
    if buttons:
        print(buttons)
    softub.button_state = buttons
    #print(softub.board_led_temp)
    #print(softub.top_led_temp)
    #print()
    buttons = 0
    text = str(softub.board_led_temp) + '\n'
    if softub.is_filter():
        text += ".5"
    if softub.is_heat():
        text += " H"
    if softub.is_filter():
        text += " F"
    label.text = text

softub = Softub(board.TX, board.RX, board.MISO, board.MOSI, callback)
up = DigitalInOut(board.D9)
up.pull = Pull.UP
jets = DigitalInOut(board.D6)
jets.pull = Pull.UP
down = DigitalInOut(board.D5)
down.pull = Pull.UP
buttons = 0
set_temperature()

while True:
    softub.poll()
    set_temperature()
    if not up.value:
        buttons |= softub.button_up
    if not down.value:
        buttons |= softub.button_down
    if not jets.value:
        buttons |= softub.button_jets
    if supervisor.runtime.serial_bytes_available:
        print('reading')
        try:
            line = input()
            line = line.split('=')
            code = line[0].upper()
            if code == 'T':
                current_temp = float(line[1])
                print('New temp', current_temp)
            elif code == 'B':
                buttons = eval(line[1])
                print('Button', buttons)
            elif code == 'F':
                softub.display_filter(eval(line[1]))
            print('done', current_temp)
        except Exception as e:
            print(e)

# SPDX-FileCopyrightText: 2023 Steve Devore steve1066d@yahoo.com
#
# SPDX-License-Identifier: MIT
# look at:
# headers:  https://www.digikey.com/short/8zw85084
# https://patents.google.com/patent/US5585025A/en
# for 5v to 3.3 v translation:  74HCT125N, 74HCT4050N
# 5v supply:  https://www.digikey.com/short/tmj9cdddd

# quick disconnect:
# https://www.digikey.com/en/products/filter/terminals/quick-connects-quick-disconnect-connectors/392


"""SoftTub temperature fiddler"""

import adafruit_ntp
import board
import digitalio
import json
import microcontroller
import mdns
import os
import rtc
import socketpool
import time
import wifi
from analogio import AnalogIn
from analogio import AnalogOut
from adafruit_httpserver import Server, Request, Response, POST
from softub import Softub
from ticks import calc_due_ticks, is_due
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_sh1107

# can try import bitmap_label below for alternative
from adafruit_display_text import label
import adafruit_displayio_sh1107


try:
    with open("test.tmp", "w") as f:
        writable = True
except OSError:
    writable = False

if writable:
    with open("config.json", "r") as f:
        config = json.load(f)
else:
    print("Could not write to nvram.  Using defaults")
    config = {
        # The target temp.
        "target_temp": 102,
        # Set to F or C for Farenheight or Celsius
        "unit": "F",
        # how often the temperature should be checked
        "poll_seconds": 1,
        # If the tub temp is below this value, it will pass the temp unchanged
        # controller
        "min_override_temp": 100,
        # The temperature to send to the controller when the pump should turn on.
        "override_on_temp": 99,
        # The temperature to send to the controller when the pump should turn off
        "override_off_temp": 105,
        # once the temp has been reached, how much must the temp
        # go down before it is turned on again
        "hysteresis": 0.5,
        # the degree increment the + and - buttons should use on the web page
        "increment": 0.5,
        # Minimum allowable target temperature
        "minimum_temp": 50,
        # Maximum allowable target temperature
        "maximum_temp": 105,
    }

# No user servicable parts below

# We don't need these so turn them off:
# i2c_power = digitalio.DigitalInOut(board.I2C_POWER)
# i2c_power.switch_to_input()
neo_power = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
neo_power.switch_to_input()

analog_in = AnalogIn(board.A2)
validate_analog = AnalogIn(board.A3)
analog_out = AnalogOut(board.A1)

# analog_out.value = 0
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

displayio.release_displays()
i2c = board.I2C()  # uses board.SCL and board.SDA
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_sh1107.SH1107(
    display_bus, width=128, height=64, rotation=0
)
display_group = displayio.Group()
display.show(display_group)
label = label.Label(terminalio.FONT, scale=1, text="Softub Controller", y=8)
display_group.append(label)

def to_F(c_deg: float):
    return c_deg * (9 / 5) + 32


def display(f_deg: float):
    return f_deg if config["unit"] == "F" else (f_deg - 32) * (5 / 9)


def set_target(deg: float):
    deg = max(deg, config["minimum_temp"])
    deg = min(deg, config["maximum_temp"])
    config["target_temp"] = deg
    softub.display_temperature(deg)
    save_config()


def get_temperature() -> float:
    x = float(analog_in.value) / 655.35 * 3.3 * 0.986199
    # print("read", analog_in.value, x, analog_in.reference_voltage)
    return x


def save_config():
    global clock
    print("Saving config")
    try:
        with open("config.json", "w") as f:
            f.write(json.dumps(config))
    except OSError:
        # ignore
        pass
        clock = 0


def set_temperature(temp: float):
    x = int(temp * 655.35 / 3.3 * 0.99206)
    # print("set temp", temp, x)
    analog_out.value = x


wifi.radio.connect(
    os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD")
)


softub = Softub(board.TX, board.RX, board.MOSI, board.MISO)
print(f"Connected to {os.getenv('CIRCUITPY_WIFI_SSID')}")
print(f"My IP address: {wifi.radio.ipv4_address}")
mdns_server = mdns.Server(wifi.radio)
hostname = os.getenv("CIRCUITPY_WEB_INSTANCE_NAME")
mdns_server.hostname = hostname
print(f"mdns name: {hostname}.local")
mdns_server.advertise_service(service_type="_http", protocol="_tcp", port=80)

pool = socketpool.SocketPool(wifi.radio)
ntp = adafruit_ntp.NTP(pool, tz_offset=-5)
server = Server(pool, "/static", debug=True)
current_temp = 0
# report this temp to the board
report_temp = 0


def webpage():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="shortcut icon" href="favicon.ico" />
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <link rel="icon" type="image/x-icon" href="favicon.ico">
    <style>
    html{{font-family: monospace; background-color: lightgrey;
    display:inline-block; margin: 0px auto; text-align: center;}}
      p{{font-size: 1rem; width: 300; word-wrap: break-word;}}
      .button{{font-family: monospace;display: inline-block;
      background-color: black; border: none;
      border-radius: 4px; color: white; padding: 16px 40px;
      text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}}
      p.dotted {{margin: auto;
      width: 95%; font-size: 18px; text-align: center;}}
    </style>
    </head>
    <body>
    <title>{hostname}</title>
    <h1>{hostname}</h1>
    <br>
    <p class="dotted">The current temperature is
    <b>{display(current_temp):.2f}°{config["unit"]}</span></b><br>
    <p class="dotted">The target temperature is
    <b>{display(config["target_temp"]):.2f}°{config["unit"]}</span></b><br>
    <p class="dotted">The CPU temperature is
    {display(to_F(microcontroller.cpu.temperature)):.0f}°{config["unit"]}</p><br>
    Increase or decrease the temp with these buttons:<br>
    <p><form accept-charset="utf-8" method="POST">
    <button class="button" name="TEMP" value="-{config["increment"]}" type="submit">-
    </button></a>
    <button class="button" name="TEMP" value="{config["increment"]}" type="submit">+
    </button></a>
    <p>
    <button class="button" name="TEMP" value="toggle" type="submit">Start
    </button></a></p>
    </body></html>
    """
    return html


@server.route("/")
def base(request: Request):
    if request.query_params.get("json") is None:
        return Response(request, webpage(), content_type="text/html")
    else:
        value = {
            "current": current_temp,
            "target": config["target_temp"],
            "cpu": to_F(microcontroller.cpu.temperature),
        }
        return Response(request, json.dumps(value), content_type="text/json")


@server.route("/", POST)
def buttonpress(request: Request):
    global clock
    if request.query_params.get("json") is None:
        temp = request.form_data["TEMP"]
        if temp == "toggle":
            softub.click_button(softub.toggle_jets)
        else:
            # set_target(config["target_temp"] + float(temp))
            print(temp)
            if float(temp) > 0:
                softub.click_button(softub.button_up)
            else:
                softub.click_button(softub.button_down)

        return Response(request, webpage(), content_type="text/html")
    else:
        value = request.json()
        print(json.dumps(value))
        # TODO
        # set_target
        # save_config()
    clock = 0
    print("set", config["target_temp"])


try:
    rtc.RTC().datetime = ntp.datetime
    print("date", time.localtime())
    server.start(str(wifi.radio.ipv4_address))
    print("Listening on http://%s:80" % wifi.radio.ipv4_address)
#  if the server fails to begin, restart the pico w
except OSError:
    time.sleep(5)
    print("restarting..")
    microcontroller.reset()

if config["unit"] == "C":
    config["min_override_temp"] = to_F(config["min_override_temp"])
    config["override_on_temp"] = to_F(config["override_on_temp"])
    config["override_off_temp"] = to_F(config["override_off_temp"])
    config["target_temp"] = to_F(config["target_temp"])
    config["hysteresis"] *= 9 / 5
    config["increment"] *= 9 / 5

temp_due = calc_due_ticks(config["poll_seconds"])
uart_clock = 0
try:
    while True:
        if is_due(temp_due):
            temp_due = calc_due_ticks(config["poll_seconds"])
            current_temp = get_temperature()
            if current_temp <= config["min_override_temp"]:
                # Allow the tub to operate normally if it hasn't hit the min temp
                # The softub controller will handle the schedule normally
                report_temp = current_temp
            else:
                adjust = (
                    0.5
                    if (config["target_temp"] == config["override_on_temp"])
                    else -0.5
                )
                adjust *= config["hysteresis"]
                under_temp = current_temp < config["target_temp"] + adjust
                if under_temp:
                    report_temp = config["override_on_temp"]
                else:
                    report_temp = config["override_off_temp"]
            set_temperature(report_temp)
            led.value = report_temp == config["override_on_temp"]
            label.text = f"{softub.debug()}\n{current_temp}\n{report_temp}"
        softub.poll()
        server.poll()
except OSError:
    time.sleep(5)
    print("restarting..")
    microcontroller.reset()

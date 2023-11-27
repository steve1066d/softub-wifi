"""Softub WiFi Adapter"""

from mqtt import mqtt_connect, mqtt_poll, mqtt_button_light
import adafruit_ntp
import board
import busio
import json
import math
import mdns
import microcontroller
import os
import rtc
import socketpool
import supervisor
import time
import wifi
import digitalio
from analogio import AnalogOut
from adafruit_httpserver import Server, Request, Response, POST
from softub import Softub
from ticks import calc_due_ticks_sec, is_due, ticks_diff, ticks_add
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn as AnalogInI2C
from analogio import AnalogIn
from adafruit_simplemath import map_unconstrained_range
import adafruit_ad569x
import traceback
import storage
from log import log

disable_httpd = False

config = None
try:
    storage.remount("/", False)
    writable = True
    with open("config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    log(e)
    writable = False
    log("Could not write to nvram.  Using defaults")
if not config:
    config = {
        # The target temp.
        "target_temp": 102,
        # Set to F or C for Farenheight or Celsius
        "unit": "F",
        # how often the temperature should be checked
        "poll_seconds": 1,
        # the degree increment the + and - buttons should use on the web page
        # and softub buttons
        "increment": 0.5,
        # Minimum allowable target temperature
        "minimum_temp": 50,
        # Maximum allowable target temperature
        "maximum_temp": 106,
        "show_settings_seconds": 5,
    }
# No user servicable parts below

A0 = board.IO1
A1 = board.IO2
A2 = board.IO3
# there seems to be a default pullup resistor that is interfering with this,
# so do this even if we we are using an i2c a2d.
analog_in = AnalogIn(A2)
dummy = AnalogIn(A1)

server = Server(None, None)
pool = None

wifi.radio.connect(
    os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD")
)
log(f"Connected to {os.getenv('CIRCUITPY_WIFI_SSID')}")
log(f"My IP address: {wifi.radio.ipv4_address}")
hostname = os.getenv("CIRCUITPY_WEB_INSTANCE_NAME")

if disable_httpd:
    log("Disabling httpd and mqtt")
else:
    for i in range(3):
        try:
            mdns_server = mdns.Server(wifi.radio)
            mdns_server.hostname = hostname
            mdns_server.advertise_service(service_type="_http", protocol="_tcp", port=80)
            log(f"mdns name: {hostname}.local")
            pool = socketpool.SocketPool(wifi.radio)
            try:
                ntp = adafruit_ntp.NTP(pool, tz_offset=-6)
                rtc.RTC().datetime = ntp.datetime
            except Exception as e:
                log(traceback.format_exception(e))
            server = Server(pool, "/static", debug=True)

            log("date", time.localtime())
            server.start(str(wifi.radio.ipv4_address))
            log("Listening on http://%s:80" % wifi.radio.ipv4_address)
            break
        except Exception as e:
            log(traceback.format_exception(e))
            time.sleep(10)

top_buttons_ms = 0
repeating = None
temp_reads = []
set_point_timeout = 0

# analog_out = AnalogOut(board.A1)

current_temp = 0
# report this temp to the board
report_temp = 0

validate_analog = None
try:
    i2c = busio.I2C(board.IO6, board.IO5)  # uses board.SCL and board.SDA
    print ("scan")
    ads = ADS.ADS1115(i2c)
    analog_in = AnalogInI2C(ads, ADS.P0)  # 0x48
    log("i2c A2D found")
    validate_analog = AnalogInI2C(ads, ADS.P1)
except Exception as e:
    log(traceback.format_exception(e))
    log("Could not find i2c adc, using internal")
try:
    analog_out = adafruit_ad569x.Adafruit_AD569x(i2c)  # 0x4C
    log("i2c DAC found")
    max_analog_out = 2.5
    # this dac is already accurate
    validate_analog = None
except Exception:
    log("Could not find i2c dac, using internal")
    # analog_out = AnalogOut(A1)
    analog_out = None
    max_analog_out = 3.3


def callback():
    global top_buttons_ms, set_point_timeout, repeating
    adjust = None
    if softub.top_buttons:
        log('button', softub.top_buttons)
        if (
            softub.top_buttons_ms != top_buttons_ms
            or repeating
            and ticks_diff(supervisor.ticks_ms(), repeating) >= 0
        ):
            if softub.top_buttons == softub.button_down:
                adjust = -config["increment"]
                log("dec")
            elif softub.top_buttons == softub.button_up:
                adjust = config["increment"]
                log("inc")
            elif softub.top_buttons == softub.button_light:
                mqtt_button_light()
            else:
                # some other button was pressed.  Just send it to the controller.
                log("buttons:", softub.top_buttons)
                softub.button_state = softub.top_buttons
                softub.button_timeout = softub.due
            # set the timer if a button is held down
            if repeating:
                repeating = ticks_add(supervisor.ticks_ms(), 300)
            else:
                repeating = ticks_add(supervisor.ticks_ms(), 2000)
    else:
        repeating = None
    top_buttons_ms = softub.top_buttons_ms
    if adjust:
        set_target(config["target_temp"] + adjust)
    tt = config["target_temp"]
    if not softub.button_timeout:
        # There is not currently a button press in process
        change = None
        if float(softub.board_led_temp) < math.floor(tt):
            change = softub.button_up
            log("change", "up")
        elif softub.board_led_temp > math.floor(tt):
            change = softub.button_down
            log("change", "down")
        if change and (softub.board_led_temp < 104 or tt < 104):
            # since 104 is the max temp, don't make the change if it is at the max.
            softub.click_button(change)
            top_buttons_ms = softub.top_buttons_ms
            log("clicked")
    # Display the current temp or the set point if there has been a recent change
    if set_point_timeout and not is_due(set_point_timeout):
        softub.display_temperature(tt)
    else:
        set_point_timeout = 0
        softub.display_temperature(current_temp)
    softub.display_heat(softub.is_heat())
    softub.display_filter(softub.is_filter());

def to_F(c_deg: float):
    return c_deg * (9 / 5) + 32


def display(f_deg: float):
    return f_deg if config["unit"] == "F" else (f_deg - 32) * (5 / 9)


def set_target(deg: float):
    global set_point_timeout
    if not deg:
        raise Exception()
    if config["target_temp"] == deg:
        return
    log(f"Changing setting to {deg}")
    deg = max(deg, config["minimum_temp"])
    deg = min(deg, config["maximum_temp"])
    config["target_temp"] = deg
    set_point_timeout = calc_due_ticks_sec(config["show_settings_seconds"])
    save_config()


def get_temperature() -> float:
    if hasattr(analog_in, "voltage"):
        x = analog_in.voltage * 100
    else:
        x = analog_in.value / 65535 * 3.3 * 100
    return x


def set_current_temp(temp: float):
    global temp_reads, current_temp
    temp_reads.append(temp)
    if len(temp_reads) > 10:
        temp_reads.pop(0)
    current_temp = sum(temp_reads) / len(temp_reads)
    return current_temp


def save_config():
    global clock
    log("Saving config")
    try:
        with open("config.json", "w") as f:
            f.write(json.dumps(config))
    except OSError:
        # ignore
        pass
        clock = 0


def set_temperature(temp: float):
    if analog_out:
        adj_out = map_unconstrained_range(temp, 98, 104, map_98, map_104)
        x = int(adj_out / max_analog_out * 655.35)
        analog_out.value = x


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

@server.route("/firmware")
def firmware(request: Request):
    os.rename("/code.py", "/code.bak")
    os.sync()
    microcontroller.reset()

@server.route("/reboot")
def reboot(request: Request):
    microcontroller.reset()

@server.route("/debug")
def base(request: Request):
    value = {
        "current": current_temp,
        "target": config["target_temp"],
        "cpu": to_F(microcontroller.cpu.temperature),
        "board": softub.board_led_temp,
        "heat": softub.is_heat(),
        "filter": softub.is_filter(),
        "output": report_temp
    }
    return Response(request, json.dumps(value), content_type="text/json")

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
            softub.click_button(softub.button_jets)
        else:
            set_target(config["target_temp"] + float(temp))
        return Response(request, webpage(), content_type="text/html")
    else:
        value = request.json()
        log(json.dumps(value))
    clock = 0
    log("set", config["target_temp"])


# Use the a2d converter to determine the actual values to use
# for the dac conversion
def _calibrate(value):
    delta = 0.0
    old_error = 100.0
    error = old_error - 1
    old_delta = 0
    while math.fabs(old_error) > math.fabs(error):
        old_error = error
        analog_out.value = int((value + delta) / 3.3 * 655.35)
        time.sleep(0.1)
        new_value = validate_analog.voltage * 100 + delta
        new_value += validate_analog.voltage * 100 + delta
        new_value /= 2
        error = value - new_value
        old_delta = delta
        delta += error
        # log("d,e", old_error, error)
    # log()
    return value + old_delta


try:
    # board 1.0 has rx & tx backwards, so reverse them
    softub = Softub(board.IO8, board.IO9, board.RX, board.TX, callback)
    if pool:
        mqtt_connect(pool, set_target)
    if validate_analog:
        map_98 = _calibrate(98.0)
        map_104 = _calibrate(104.0)
        log(f"Calibrated adjustments 98={map_98}, 104={map_104}")
    else:
        map_98 = 98
        map_104 = 104
        log("Not using i2c adc with internal dac, no calibration")

    if config["unit"] == "C":
        config["target_temp"] = to_F(config["target_temp"])
        config["hysteresis"] *= 9 / 5
        config["increment"] *= 9 / 5
    temp_due = calc_due_ticks_sec(config["poll_seconds"])
    uart_clock = 0

    while True:
        tt = config["target_temp"]
        if is_due(temp_due):
            temp_due = calc_due_ticks_sec(config["poll_seconds"])
            temp = get_temperature()
            set_current_temp(temp)
            # Adjusts the reported temp to account for > 104 temps,
            # and fraction of degree settings.
            report_temp = current_temp - (tt - int(min(104, tt)))
            set_temperature(report_temp)
            #led.value(current_temp <= tt)
        softub.poll()
        if pool:
            server.poll()
            mqtt_poll(current_temp, tt)
except Exception as e:
    log(traceback.format_exception(e))
    time.sleep(30)
    log("restarting..")
    supervisor.reload()

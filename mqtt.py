import os
from ticks import calc_due_ticks_sec, is_due, ticks_add
import adafruit_logging as logging
import time
import traceback
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from log import log
import gc

MQTT_POLL_SEC = 60

mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_key = os.getenv("MQTT_PASSWORD")
device = os.getenv("MQTT_DEVICE")
mqtt_broker = os.getenv("MQTT_BROKER")

temperature_feed = f"homeassistant/sensor/{device}/temperature"
set_temp_feed = f"homeassistant/climate/{device}/set"
temperature_setting_feed = f"homeassistant/sensor/{device}/setting"
button_feed = f"hottub/switch1/command"

mqtt_due = 0
mqtt_temp = 0
mqtt_set_temp = 0
mqtt_error = False

def connected(client, userdata, flags, rc):
    log("Connected to mqtt")

def disconnected(client, userdata, rc):
    log("Disconnected from mqtt")

def message(client, topic, message):
    global mqtt_due
    if topic == set_temp_feed:
        fn_set_temp(float(message))
        mqtt_due = calc_due_ticks_sec(.2)
    log(f"New message on topic {topic}: {message}")

def mqtt_connect(pool, _set_temp):
    global mqtt_client, mqtt_due, fn_set_temp
    mqtt_client = MQTT.MQTT(
        broker=mqtt_broker,
        port=1883,
        username=mqtt_username,
        password=mqtt_key,
        socket_pool=pool,
        socket_timeout=1,
        connect_retries=1,
    )

    #mqtt_client.enable_logger(logging, logging.DEBUG)
    mqtt_client.on_connect = connected
    mqtt_client.on_disconnect = disconnected
    mqtt_client.on_message = message
    fn_set_temp = _set_temp
    try:
        for i in range(3):
            try:
                mqtt_client.connect()
                mqtt_due = calc_due_ticks_sec(2)
                mqtt_client.subscribe(set_temp_feed)
                mqtt_client.loop(.5)
                mqtt_client.subscribe(temperature_feed)
                mqtt_client.loop(.5)
                mqtt_client.subscribe(f"homeassistant/state/{device}/state_heat")
                mqtt_client.loop(.5)
                # This is set by homeassistant
                # mqtt_client.publish(f"homeassistant/state/{device}/state_heat", "heat", True)
                mqtt_client.loop(.5)
                break
            except MQTT.MMQTTException as e:
                log(traceback.format_exception(e))
                time.sleep(.3)
    except MQTT.MMQTTException as e:
        log(traceback.format_exception(e))
        time.sleep(3)
        mqtt_client = None

def mqtt_button_light():
    mqtt_client.publish(button_feed, "press")
    log("published light button")

def mqtt_poll(_temp, _set_temp):
    global mqtt_temp, mqtt_set_temp, mqtt_due, mqtt_error
    if not mqtt_client:
        return
    try:
        if mqtt_client.is_connected():
            # Poll the message queue
            mqtt_client.loop()
        if is_due(mqtt_due):
            log("mem:", gc.mem_free())
        # Process every minute or if there's a change in the set point
        if is_due(mqtt_due) or not mqtt_error and _set_temp != mqtt_set_temp:
            log(_set_temp, _temp)
            if not mqtt_client.is_connected():
                mqtt_client.reconnect()
            if mqtt_client.is_connected():
                try:
                    _temp = round(_temp, 1)
                    _set_temp = round(_set_temp, 1)
                    if _temp != mqtt_temp:
                        mqtt_temp = _temp
                        mqtt_client.publish(temperature_feed, mqtt_temp, True)
                    if _set_temp != mqtt_set_temp:
                        mqtt_set_temp = _set_temp
                        mqtt_client.publish(temperature_setting_feed, mqtt_set_temp, True)
                        mqtt_set_updated = False
                        log("pub set", mqtt_set_temp)
                except:
                    pass
            mqtt_due = ticks_add(mqtt_due, 60000)
            mqtt_error = False
    except MQTT.MMQTTException as e:
        mqtt_error = True
        mqtt_due = calc_due_ticks_sec(300)
        log(traceback.format_exception(e))
    except BrokenPipeError as e:
        mqtt_error = True
        mqtt_due = calc_due_ticks_sec(300)
        log(traceback.format_exception(e))

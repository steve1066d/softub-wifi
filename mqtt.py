import os
from ticks import calc_due_ticks_sec, is_due, ticks_add
import time
import traceback
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from log import log

MQTT_POLL_SEC = 60

mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_key = os.getenv("MQTT_PASSWORD")
device = os.getenv("MQTT_DEVICE")
mqtt_broker = os.getenv("MQTT_BROKER")

temperature_command_topic = f"{device}/command/temperature"
temperature_state_topic = f"{device}/state/temperature"

mode_command_topic = f"{device}/command/mode"
mode_state_topic = f"{device}/state/mode"

current_temperature_topic = f"{device}/state/current"

# This exposes the Softub Light button to mqtt
button_feed = "hottub/switch1/command"

states = {}

mqtt_due = 0
mqtt_error = False
# We use the mode as an indication if the hot tub is on.  This can be turned on or off
# by monitoring the power. If this or the board is in filter or heat mode, then this
# will be on.
heat_state = False


def connected(client, userdata, flags, rc):
    log("Connected to mqtt")


def disconnected(client, userdata, rc):
    log("Disconnected from mqtt")


def publish_if_changed(topic, value, persistent=False):
    current = states.get(topic)
    if current != value:
        mqtt_client.publish(topic, value, persistent)
        states[topic] = value
        log(f"{topic} set to {value}")

def message(client, topic, message):
    global mqtt_due, heat_state
    log(f"New message on topic {topic}: {message}")
    if topic == temperature_command_topic:
        fn_set_temp(float(message))
        mqtt_due = calc_due_ticks_sec(0.2)
    elif topic == mode_command_topic:
        heat_state = message == "heat"
        mqtt_due = calc_due_ticks_sec(0.2)


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

    # mqtt_client.enable_logger(logging, logging.DEBUG)
    mqtt_client.on_connect = connected
    mqtt_client.on_disconnect = disconnected
    mqtt_client.on_message = message
    fn_set_temp = _set_temp
    try:
        for i in range(3):
            try:
                mqtt_client.connect()
                mqtt_due = calc_due_ticks_sec(2)
                mqtt_client.subscribe(temperature_command_topic)
                mqtt_client.loop(0.5)
                mqtt_client.subscribe(mode_command_topic)
                mqtt_client.loop(0.5)
                break
            except MQTT.MMQTTException as e:
                log(traceback.format_exception(e))
                time.sleep(0.3)
    except MQTT.MMQTTException as e:
        log(traceback.format_exception(e))
        time.sleep(3)
        mqtt_client = None


def mqtt_button_light():
    mqtt_client.publish(button_feed, "press")
    log("published light button")

def mqtt_poll(_temp, _set_temp, _running):
    global mqtt_due, mqtt_error
    if not mqtt_client:
        return
    try:
        if mqtt_client.is_connected():
            # Poll the message queue
            mqtt_client.loop()
        # Process every minute or if there's a change in the set point
        if is_due(mqtt_due) or (
            not mqtt_error and states.get(temperature_state_topic) != _set_temp
        ):
            if not mqtt_client.is_connected():
                mqtt_client.reconnect()
            if mqtt_client.is_connected():
                try:
                    publish_if_changed(current_temperature_topic, round(_temp, 1), True)
                    publish_if_changed(
                        temperature_state_topic, round(_set_temp, 1), True
                    )
                    # report heat if home assistant reports the heat is on, or if the
                    # heat or filter indicators are on.
                    publish_if_changed(
                        mode_state_topic, "heat" if heat_state or _running else "off"
                    )
                except Exception:
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

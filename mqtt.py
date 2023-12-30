import os
from ticks import calc_due_ticks_sec, is_due
import traceback
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from log import log, log_close
import wifi
import microcontroller

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

_connected = False
_mqtt_due = 0
_mqtt_retry_due = None
_softub = None
# We use the mode as an indication if the hot tub is on.  This can be turned on or off
# by monitoring the power. If this or the board is in filter or heat mode, then this
# will be on.
power_state = False
callback = None

def is_running():
    return _softub and _softub.is_running() or power_state


def _publish_if_changed(topic, value, persistent=False):
    current = states.get(topic)
    if current != value:
        mqtt_client.publish(topic, value, persistent)
        states[topic] = value
        log(f"{topic} set to {value}")
        return True
    return False

def _message(client, topic, message):
    global power_state
    if topic == temperature_command_topic:
        log(f"New message on topic {topic}: {message}")
        fn_set_temp(float(message))
    elif topic == mode_command_topic:
        if message.startswith("power"):
            new_state = message == "power_on"
            if new_state != power_state:
                power_state = new_state
                log(f"New message on topic {topic}: {message}")
        else:
            request = message == "heat"
            if request != is_running():
                _softub.click_button(_softub.button_jets)
            log(f"New message on topic {topic}: {message}")


def mqtt_init(pool, _set_temp, __softub, _callback):
    global mqtt_client, fn_set_temp, _softub, callback, _connected, _mqtt_due
    mqtt_client = MQTT.MQTT(
        broker=mqtt_broker,
        port=1883,
        username=mqtt_username,
        password=mqtt_key,
        socket_pool=pool,
        socket_timeout=1,
        connect_retries=1,
    )
    callback = _callback
    # mqtt_client.enable_logger(logging, logging.DEBUG)
    mqtt_client.on_message = _message
    fn_set_temp = _set_temp
    _softub = __softub
    try:
        mqtt_client.connect()
        _mqtt_due = calc_due_ticks_sec(2)
        mqtt_client.subscribe(temperature_command_topic)
        mqtt_client.loop(0.5)
        mqtt_client.subscribe(mode_command_topic)
        mqtt_client.loop(0.5)
        _connected = True
    except Exception as e:
        log(traceback.format_exception(e))
        raise e


def mqtt_poll(_temp, _set_temp):
    global _mqtt_retry_due, _mqtt_due, _connected
    if not mqtt_client:
        return
    try:
        if _mqtt_retry_due and not is_due(_mqtt_retry_due):
            return
        _mqtt_retry_due = None
        if not _connected or not mqtt_client.is_connected():
            _wifi = False
            try:
                log(wifi.radio.ipv4_gateway, wifi.radio.ap_active, wifi.radio.ap_info)
                _ping = wifi.radio.ping(wifi.radio.ipv4_gateway)
                if _ping is not None:
                    _wifi = True
            except Exception as e:
                log(traceback.format_exception(e))
            if not _wifi:
                log("WiFi not connected.  Restarting")
                log_close()
                microcontroller.reset()
            mqtt_client.reconnect()
            if mqtt_client.is_connected:
                _connected = True
                log("reconnected")

        # Poll the message queue
        mqtt_client.loop()
        _publish_if_changed(button_feed, _softub.get_buttons())
        if _publish_if_changed(mode_state_topic, "heat" if is_running() else "off"):
            callback(is_running())
        _publish_if_changed(temperature_state_topic, round(_set_temp, 1), True)
        if is_due(_mqtt_due):
            _publish_if_changed(current_temperature_topic, round(_temp, 1), True)
            _mqtt_due = calc_due_ticks_sec(MQTT_POLL_SEC)
    except Exception as e:
        _connected = False
        _mqtt_retry_due = calc_due_ticks_sec(300)
        log(traceback.format_exception(e))

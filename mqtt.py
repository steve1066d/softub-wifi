import os
from ticks import calc_due_ticks_sec, is_due, ticks_add
import adafruit_logging as logging
import time
import traceback
import adafruit_minimqtt.adafruit_minimqtt as MQTT
MQTT_POLL_SEC = 60

mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_key = os.getenv("MQTT_PASSWORD")

# Setup a feed named 'photocell' for publishing to a feed
temperature_feed = "homeassistant/sensor/hottub/temperature"
set_temp_feed = "homeassistant/climate/hottub/set"
temperature_setting_feed = "homeassistant/sensor/hottub/setting"
button_feed = "hottub/switch1/command"

mqtt_due = 0
mqtt_temp = 0
mqtt_set_temp = 0
mqtt_error = False
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Connected to mqtt")

def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from Adafruit IO!")

def message(client, topic, message):
    global mqtt_due
    # This method is called when a topic the client is subscribed to

    # has a new message.
    if topic == set_temp_feed:
        fn_set_temp(float(message))
        mqtt_due = calc_due_ticks_sec(.2)

    print(f"New message on topic {topic}: {message}")

def mqtt_connect(pool, _set_temp):
    global mqtt_client, mqtt_due, fn_set_temp
    mqtt_client = MQTT.MQTT(
        broker="192.168.1.193",
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
                mqtt_client.subscribe("homeassistant/state/hottub/state_heat")
                mqtt_client.loop(.5)
                mqtt_client.publish("homeassistant/state/hottub/state_heat", "heat", True)
                mqtt_client.loop(.5)
                break
            except MQTT.MMQTTException as e:
                traceback.print_exception(e)
                time.sleep(.3)
    except MQTT.MMQTTException as e:
        traceback.print_exception(e)
        time.sleep(3)
        mqtt_client = None

def mqtt_button_light():
    mqtt_client.publish(button_feed, "press")

def mqtt_poll(_temp, _set_temp):
    global mqtt_temp, mqtt_set_temp, mqtt_due, mqtt_error
    if not mqtt_client:
        return
    try:
        if mqtt_client.is_connected():
            # Poll the message queue
            mqtt_client.loop()
        # Process every minute or if there's a change in the set point
        if is_due(mqtt_due) or not mqtt_error and _set_temp != mqtt_set_temp:
            print(_set_temp, _temp)
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
                        print("pub set", mqtt_set_temp)
                except:
                    pass
            mqtt_due = ticks_add(mqtt_due, 60000)
            mqtt_error = False
    except MQTT.MMQTTException as e:
        mqtt_error = True
        mqtt_due = calc_due_ticks_sec(300)
        traceback.print_exception(e)
    except BrokenPipeError as e:
        mqtt_error = True
        mqtt_due = calc_due_ticks_sec(300)
        traceback.print_exception(e)

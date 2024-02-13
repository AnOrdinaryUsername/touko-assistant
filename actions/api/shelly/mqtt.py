import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from datetime import datetime, timezone

import logging
import os
import json

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

def on_connect(client, user_data, flags, reason_code, properties):
    print("reason_code: " + str(reason_code))


def on_message(client, user_data, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    # Temperature, Humidity, and Battery % reading from Shelly H&T device
    device_reading = json.loads(msg.payload.decode("utf-8"))
    json_file = os.path.join(os.path.dirname(__file__), 'gen3_ht_data.json')

    # Get previous readings from json file
    with open(json_file) as file:
        json_data = json.load(file)

    logging.debug(f"Data on file: {json.dumps(json_data, indent=2)}")
    logging.debug(f"Reading from H&T: {json.dumps(device_reading, indent=2)}")

    # Get current datetime in UTC
    dt = datetime.now(timezone.utc)

    # Add local timezone information to datetime
    tz_dt = dt.astimezone()

    # Get current iso 8601 format datetime string including the default timezone
    iso_date = tz_dt.isoformat()
    json_data["updatedAt"] = iso_date

    if "devicepower" in msg.topic:
        json_data["battery"] = device_reading["battery"]["percent"]
        json_data["isCharging"] = device_reading["external"]["present"]

    elif "temperature" in msg.topic:
        json_data["tC"] = device_reading["tC"]
        json_data["tF"] = device_reading["tF"]

    elif "humidity" in msg.topic:
        json_data["rh"] = device_reading["rh"]

    # Update previous readings with new reading data
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=4)

    logging.debug("Finished writing data to JSON file.")


def on_subscribe(client, user_data, mid, reason_code_list, properties):
    print("Subscribed: " + str(mid) + " " + str(reason_code_list))

"""
                            +----------------+
+---------------+           |                |
|               |           |                |  Subscribe  +--------+
| Shelly Gen 3  |  Publish  |                |<------------+        |
|      H&T      +---------->|   MQTT Broker  |             | Device |
|               |           |                +------------>|        |
+---------------+           |                |   Publish   +--------+
                            |                |
                            +----------------+
"""

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe

device_id = os.environ['SHELLY_HT_DEVICE_ID']
broker = os.environ['MQTT_BROKER']

"""
Check if broker is getting published data by using MQTT Explorer.
Link: https://mqtt-explorer.com/

1) Enable MQTT in Shelly settings
2) Add MQTT broker host and port to MQTT Explorer
3) In MQTT Explorer, go to Advanced -> Add topic with device like "shellyhtg3/#"
   (if you have the prefix thing) -> Connect

Should show broker host + shelly topic. Status updates occasionally appear after >1 hour.
"""

mqttc.connect(host=broker, port=1883)

"""
The tuple means (Topic, QoS level).

Topics are message routes for communicating and receiving information.
QoS (Quality of Service) determines the level of delivery guarantee.

QoS level 1 is used because I want to guarantee I get the message at least
once and duplicate messages aren't an issue.

See links:
https://cedalo.com/blog/mqtt-topics-and-mqtt-wildcards-explained/#What_are_MQTT_Topics
https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/
"""
mqttc.subscribe(topic=[
        (f'{device_id}/status/temperature:0', 1), 
        (f'{device_id}/status/humidity:0', 1),
        (f'{device_id}/status/devicepower:0', 1) 
    ]
)

mqttc.loop_forever()

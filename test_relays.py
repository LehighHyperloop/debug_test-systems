# sends a series of random commands in quick succession
# to the arduino control relays, to test their ability to
# handle a large series of commands
import random
import os
import paho.mqtt.client as mqtt
import time
import json
import sys

subsystems = {"fan": ["STOPPED", "RUNNING"], "compressor": ["STOPPED", "RUNNING"], \
                "wheels": ["UP", "DOWN"], "braking": ["OFF", "ON"], "levitation": \
                ["STOPPED", "RUNNING"], "propulsion": ["STOPPED", "RUNNING"]}
expected = {"fan": None, "compressor": None, "wheels": None, "braking": None, "levitation": None, "propulsion": None}
actual = {"fan": None, "compressor": None, "wheels": None, "braking": None, "levitation": None, "propulsion": None}

#set up client
client = mqtt.Client()
mqtt_IP = os.environ["MQTT_IP"]
client.connect(mqtt_IP, 1883)
client.loop_start()

for system in subsystems.keys():
    client.subscribe("subsystem/" + system + "/#")

#handle response. Will later check if the reponse is good
def on_message(mosq, obj, msg):
    topic_split = msg.topic.split("/")
    if topic_split[len(topic_split) - 1] == "set": #check if last space in topic is "set"
        return #ignore own set messages

    print msg.topic, "RESPONSE:", msg.payload

    response = json.loads(msg.payload)
    if "state" in response:
        actual[topic_split[1]] = response["state"]


client.on_message = on_message

# Loop in main
command_dict = {}
try:
    while True:
        subsystem = random.choice(subsystems.keys())
        if subsystem == "propulsion":  
            continue
        command = random.choice(subsystems[subsystem])
        command_dict["t_state"] = command
        print "Setting {} to state {}".format(subsystem, command)
        expected[subsystem] = command
        start = time.time()
        client.publish("subsystem/" + subsystem + "/set", json.dumps(command_dict))
        while True:
            if expected[subsystem] == actual[subsystem]:
                break
            if time.time() - start > 4:
                break
            time.sleep(.1)

        if expected[subsystem] == actual[subsystem]:
            print("[GOOD] "+ subsystem + "->" + command)
        else:
            print("[BAD] " + subsystem + "->" + command)
            sys.exit()

except KeyboardInterrupt:
    print("Shutting down...")
    print("Done!")

client.loop_stop()

import time
import json
import paho.mqtt.client as mqtt
from util import create_data

BROKER = "localhost"
PORT = 1883
TOPIC = "comp216/data"


def main():
    client = mqtt.Client()   # create client
    client.connect(BROKER, PORT)
    print("[Publisher] Connected to MQTT broker.")

    for i in range(10):  # send 10 transmissions
        payload = create_data()         # dict
        json_string = json.dumps(payload)  # convert to string

        client.publish(TOPIC, json_string)  # publish
        print(f"[Publisher] Sent packet #{payload['id']}")

        time.sleep(1) 

    client.disconnect()
    print("[Publisher] Connection closed.")


if __name__ == "__main__":
    main()

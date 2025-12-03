import json
import paho.mqtt.client as mqtt
from util import print_data

BROKER = "localhost"
PORT = 1883
TOPIC = "comp216/data"


#  MESSAGE HANDLER
def on_message(client, userdata, message):
    decoded = message.payload.decode("utf-8")     # decode bytes -> str
    data_dict = json.loads(decoded)               # convert JSON -> dict
    print_data(data_dict)                         # print nicely


#  MAIN SUBSCRIBER SETUP
def main():
    client = mqtt.Client()
    client.on_message = on_message       # wire up handler

    client.connect(BROKER, PORT)
    print("[Subscriber] Connected to broker.")

    client.subscribe(TOPIC)
    print(f"[Subscriber] Subscribed to: {TOPIC}")

    print("[Subscriber] Waiting for messages...")
    client.loop_forever()  # blocking loop


if __name__ == "__main__":
    main()

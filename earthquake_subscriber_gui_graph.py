import json
import paho.mqtt.client as mqtt
import tkinter as tk
from earthquake_dynamic_line_chart import DynamicLineChart

class EarthquakeSubscriber:
    def __init__(self, chart, broker_host='localhost', broker_port=1883, topic='movement/channel1'):
        self.chart = chart
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.topic = topic

        self.client.connect(broker_host, broker_port)
        self.client.subscribe(self.topic)
        self.client.loop_start()

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode('utf-8'))
            magnitude = float(data.get('magnitude', 0.0))
            self.chart.add_value(magnitude)
        except Exception as e:
            print("Error processing message:", e)


def main():
    root = tk.Tk()
    chart = DynamicLineChart(root)
    
    # Subscriber updates chart dynamically
    subscriber = EarthquakeSubscriber(chart, topic='movement/channel1')
    
    root.mainloop()


if __name__ == "__main__":
    main()


'''
import paho.mqtt.client as mqtt
def on_message(client, userdata, message):
    print(f'\n{message.topic} \n{message.payload.decode("utf-8")}\n')
client = mqtt.Client() #instantiates a client
client.on_message = on_message #wire-up the on_message handler
client.connect('localhost', 1883) #connects to the server
client.subscribe('movement/channel1') # topic to subscribe to
while True:
    client.loop_forever() #keep the client alive
'''
 
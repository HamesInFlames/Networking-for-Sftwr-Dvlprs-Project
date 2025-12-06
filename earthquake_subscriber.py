import json
import paho.mqtt.client as mqtt
import tkinter as tk
from earthquake_dynamic_line_chart import DynamicLineChart

class EarthquakeSubscriber:
    def __init__(self, chart, broker_host='localhost', broker_port=1883, topic='movement/California'):
        self.chart = chart
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.topic = topic

        self.client.connect(broker_host, broker_port)
        self.client.subscribe(self.topic)
        self.client.loop_start()

    def change_topic(self, new_topic):
        # unsubscribe from old topic and subscribe to new topic
        if self.topic:
            self.client.unsubscribe(self.topic)
        self.topic = new_topic
        self.client.subscribe(self.topic)
        self.chart.clear()  # Clear chart on topic change
        print(f"Subscribed to topic: {self.topic}")

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode('utf-8'))
            magnitude = float(data.get('magnitude', 0.0))
            self.chart.add_value(magnitude)
        except Exception as e:
            print("Error processing message:", e)


def main():
    root = tk.Tk()
    root.title("Earthquake Magnitude Subscriber")

    # Topic selection drop-down
    topic_var = tk.StringVar(value='movement/California')
    topics = ["movement/BritishColumbia", "movement/California", "movement/Tokyo"]
    topic_menu = tk.OptionMenu(root, topic_var, *topics, 
                               command=lambda val: subscriber.change_topic(val))
    topic_menu.pack(pady=10)

    # Dynamic line chart
    chart = DynamicLineChart(root)
    
    # Subscriber updates chart dynamically
    subscriber = EarthquakeSubscriber(chart, topic='movement/California')

    root.mainloop()


if __name__ == "__main__":
    main()

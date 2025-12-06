"""
Earthquake Subscriber Module

This module subscribes to MQTT topics and displays earthquake magnitude
data in real-time using a dynamic line chart.

The subscriber:
- Connects to an MQTT broker (Mosquitto)
- Subscribes to earthquake data topics
- Parses JSON messages containing magnitude data
- Updates the chart with new readings

Author: Group Assignment - COMP216
Date: Fall 2025
"""

import json
import paho.mqtt.client as mqtt
import tkinter as tk
from earthquake_dynamic_line_chart import DynamicLineChart


class EarthquakeSubscriber:
    """
    MQTT Subscriber that receives earthquake data and updates the chart.
    
    This class handles:
    - Connecting to the MQTT broker
    - Subscribing/unsubscribing to topics
    - Processing incoming messages
    - Passing data to the chart for visualization
    """
    
    def __init__(self, chart, broker_host='localhost', broker_port=1883, topic='movement/California'):
        """
        Initialize the subscriber.
        
        Args:
            chart: DynamicLineChart instance to update with data
            broker_host: MQTT broker hostname (default: localhost)
            broker_port: MQTT broker port (default: 1883)
            topic: Initial topic to subscribe to
        """
        self.chart = chart  # Reference to the chart widget
        
        # Create MQTT client instance
        self.client = mqtt.Client()
        
        # Set callback function for when messages arrive
        self.client.on_message = self.on_message
        
        # Store current topic
        self.topic = topic

        # Connect to the MQTT broker
        self.client.connect(broker_host, broker_port)
        
        # Subscribe to the initial topic
        self.client.subscribe(self.topic)
        
        # Start the network loop in a background thread
        # This handles incoming messages asynchronously
        self.client.loop_start()

    def change_topic(self, new_topic):
        """
        Switch to a different MQTT topic (region).
        
        This method:
        1. Unsubscribes from the old topic
        2. Subscribes to the new topic
        3. Clears the chart to show fresh data
        
        Args:
            new_topic: New topic string to subscribe to
        """
        # Unsubscribe from current topic
        if self.topic:
            self.client.unsubscribe(self.topic)
        
        # Update to new topic
        self.topic = new_topic
        self.client.subscribe(self.topic)
        
        # Clear old data from chart
        self.chart.clear()
        
        print(f"Subscribed to topic: {self.topic}")

    def on_message(self, client, userdata, message):
        """
        Callback function - called when an MQTT message is received.
        
        This method:
        1. Decodes the message payload (JSON)
        2. Extracts the magnitude value
        3. Sends it to the chart
        
        Args:
            client: MQTT client instance
            userdata: User-defined data (not used)
            message: MQTT message object containing topic and payload
        """
        try:
            # Decode JSON payload from bytes to string, then parse
            data = json.loads(message.payload.decode('utf-8'))
            
            # Extract magnitude value (default to 0.0 if not found)
            magnitude = float(data.get('magnitude', 0.0))
            
            # Send value to chart for display
            self.chart.add_value(magnitude)
            
        except Exception as e:
            # Log any errors (JSON parsing, etc.)
            print("Error processing message:", e)


def main():
    """
    Main function - sets up and runs the subscriber GUI.
    
    Creates:
    - Main window with region dropdown
    - Dynamic line chart
    - MQTT subscriber
    """
    # Create main Tkinter window
    root = tk.Tk()
    root.title("Earthquake Magnitude Monitor")
    
    # ===========================================
    # TOPIC SELECTION DROPDOWN
    # ===========================================
    # Frame to hold the dropdown
    frame = tk.Frame(root)
    frame.pack(pady=10)
    
    # Label for the dropdown
    tk.Label(frame, text="Region:").pack(side="left", padx=5)
    
    # Variable to store selected topic
    topic_var = tk.StringVar(value='movement/California')
    
    # Available topics (regions)
    topics = ["movement/BritishColumbia", "movement/California", "movement/Tokyo"]
    
    # Create dropdown menu
    topic_menu = tk.OptionMenu(frame, topic_var, *topics)
    topic_menu.pack(side="left")
    
    # ===========================================
    # CHART
    # ===========================================
    # Create the dynamic line chart (max 100 data points)
    chart = DynamicLineChart(root, max_points=100)
    
    # ===========================================
    # SUBSCRIBER
    # ===========================================
    # Create MQTT subscriber - connects to broker and starts receiving data
    subscriber = EarthquakeSubscriber(chart, topic='movement/California')
    
    # ===========================================
    # TOPIC CHANGE HANDLER
    # ===========================================
    def on_topic_change(*args):
        """Called when user selects a different region from dropdown."""
        subscriber.change_topic(topic_var.get())
    
    # Bind the handler to the variable (fires when value changes)
    topic_var.trace("w", on_topic_change)

    # ===========================================
    # START THE GUI
    # ===========================================
    # Run the Tkinter event loop (blocks until window is closed)
    root.mainloop()


# Entry point - run main() when script is executed directly
if __name__ == "__main__":
    main()

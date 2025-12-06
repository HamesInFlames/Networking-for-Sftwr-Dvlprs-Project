"""
Earthquake Publisher Module

This module publishes earthquake magnitude data to MQTT topics.
It provides a GUI for controlling the data generation and publishing.

Features:
- Topic selection (different regions)
- Configurable number of readings and interval
- Skip positions to simulate missing data
- Mainshock magnitude slider
- Background movement vs Main Shock modes

Author: Group Assignment - COMP216
Date: Fall 2025
"""

import tkinter as tk
from tkinter import messagebox
import json
import random
import time
import paho.mqtt.client as mqtt
from earthquake_data_generator import EarthquakeMagnitudeGenerator


# ===========================================
# MQTT PUBLISHER CLASS
# ===========================================
class EarthquakePublisher:
    """
    Handles MQTT connection and message publishing.
    
    This class manages:
    - Connecting to the MQTT broker
    - Publishing JSON payloads
    - Disconnecting cleanly
    """
    
    def __init__(self, broker_host='localhost', broker_port=1883):
        """
        Initialize the publisher.
        
        Args:
            broker_host: MQTT broker hostname (default: localhost)
            broker_port: MQTT broker port (default: 1883 for Mosquitto)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = None       # MQTT client instance
        self.generator = None    # EarthquakeMagnitudeGenerator instance

    def connect(self):
        """
        Connect to the MQTT broker and start the network loop.
        """
        # Create new MQTT client
        self.client = mqtt.Client()
        
        # Connect to broker
        self.client.connect(self.broker_host, self.broker_port)
        
        # Start background thread for network traffic
        self.client.loop_start()
        
        print(f"[Publisher] Connected to {self.broker_host}:{self.broker_port}")

    def disconnect(self):
        """
        Disconnect from the MQTT broker cleanly.
        """
        if self.client:
            # Stop the network loop
            self.client.loop_stop()
            
            # Disconnect from broker
            self.client.disconnect()
            
            print("[Publisher] Disconnected")


# ===========================================
# GUI CLASS
# ===========================================
class EarthquakeGUI:
    """
    Graphical User Interface for the earthquake publisher.
    
    Provides controls for:
    - Selecting MQTT topic (region)
    - Setting number of readings to publish
    - Setting interval between readings
    - Setting number of readings to skip (simulate missing data)
    - Adjusting mainshock magnitude via slider
    - Starting/stopping publishing
    """
    
    def __init__(self, root):
        """
        Initialize the GUI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        
        # ===========================================
        # STATE VARIABLES
        # ===========================================
        self.publisher = None          # EarthquakePublisher instance
        self.is_publishing = False     # Whether currently publishing
        self.current_reading = 0       # Current reading number
        self.total_readings = 0        # Total readings to publish
        self.interval_ms = 0           # Interval between readings (milliseconds)
        self.publish_params = {}       # Parameters for publishing
        
        # Skip positions - simulates missing/corrupted data
        self.skip_count = 3            # Number of readings to skip
        self.skip_positions = set()    # Set of reading indices to skip

        # Build the GUI
        self.setup_gui()

    def setup_gui(self):
        """
        Build all GUI components.
        Creates frames, labels, entries, buttons, and slider.
        """
        # ===========================================
        # WINDOW SETUP
        # ===========================================
        self.root.title("Earthquake Data Publisher")
        self.root.geometry("460x560")
        self.root.configure(bg="#f5f5f5")  # Light gray background

        # ===========================================
        # TITLE
        # ===========================================
        title = tk.Label(
            self.root,
            text="Earthquake Data Publisher",
            font=("Segoe UI", 18, "bold"),
            bg="#f5f5f5",
            fg="#333",
        )
        title.pack(pady=(15, 10))

        # ===========================================
        # HELPER FUNCTION FOR STYLED FRAMES
        # ===========================================
        def modern_frame(parent):
            """Create a styled frame with white background and border."""
            return tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)

        # ===========================================
        # TOPIC SELECTION
        # ===========================================
        frame_topic = modern_frame(self.root)
        frame_topic.pack(pady=5, fill="x", padx=15)

        # Configure grid columns
        frame_topic.columnconfigure(0, weight=0)  # Label column (fixed width)
        frame_topic.columnconfigure(1, weight=1)  # Dropdown column (expands)

        # Topic label
        tk.Label(frame_topic, text="Topic:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        
        # Topic variable (stores selected value)
        self.topic_var = tk.StringVar(value="movement/California")

        def on_topic_change(selected_topic):
            """Handle topic selection change."""
            self.stop_publishing()  # Stop any current publishing
            self.topic_var.set(selected_topic)

        # Topic dropdown menu
        topic_menu = tk.OptionMenu(
            frame_topic, 
            self.topic_var, 
            "movement/BritishColumbia", 
            "movement/California", 
            "movement/Tokyo",
            command=on_topic_change
        )
        topic_menu.config(width=25, bg="#fafafa", relief="flat")
        topic_menu.grid(row=0, column=1, padx=8, sticky="e") 

        # ===========================================
        # NUMBER OF READINGS INPUT
        # ===========================================
        frame_count = modern_frame(self.root)
        frame_count.pack(pady=5, fill="x", padx=15)

        frame_count.columnconfigure(0, weight=0)
        frame_count.columnconfigure(1, weight=1)

        tk.Label(frame_count, text="Number of readings:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0)
        
        # Entry field for reading count
        self.count_entry = tk.Entry(frame_count, width=12, relief="flat", highlightthickness=1, highlightbackground="#ccc")
        self.count_entry.insert(0, "100")  # Default value
        self.count_entry.grid(row=0, column=1, padx=8, sticky="e")

        # ===========================================
        # INTERVAL INPUT
        # ===========================================
        frame_interval = modern_frame(self.root)
        frame_interval.pack(pady=5, fill="x", padx=15)

        frame_interval.columnconfigure(0, weight=0)
        frame_interval.columnconfigure(1, weight=1)

        tk.Label(frame_interval, text="Interval (seconds):", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0)
        
        # Entry field for interval
        self.interval_entry = tk.Entry(frame_interval, width=12, relief="flat", highlightthickness=1, highlightbackground="#ccc")
        self.interval_entry.insert(0, "0.5")  # Default: 0.5 seconds
        self.interval_entry.grid(row=0, column=1, padx=8, sticky="e")

        # ===========================================
        # SKIP COUNT INPUT
        # ===========================================
        # This simulates missing data (sensor failures, network issues)
        frame_skip = modern_frame(self.root)
        frame_skip.pack(pady=5, fill="x", padx=15)

        frame_skip.columnconfigure(0, weight=0)
        frame_skip.columnconfigure(1, weight=1)

        tk.Label(frame_skip, text="Number of readings to skip:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0)
        
        # Entry field for skip count
        self.skip_entry = tk.Entry(frame_skip, width=12, relief="flat", highlightthickness=1, highlightbackground="#ccc")
        self.skip_entry.insert(0, "3")  # Default: skip 3 readings
        self.skip_entry.grid(row=0, column=1, padx=8, sticky="e")

        # ===========================================
        # MAINSHOCK MAGNITUDE SLIDER
        # ===========================================
        frame_mainshock = modern_frame(self.root)
        frame_mainshock.pack(pady=5, fill="x", padx=15)

        tk.Label(frame_mainshock, text="Mainshock Magnitude:", bg="#ffffff", font=("Segoe UI", 10)).pack(side="left")
        
        # Slider variable (stores current value)
        self.mainshock_mag_var = tk.DoubleVar(value=7.0)
        
        # Slider widget
        self.mainshock_slider = tk.Scale(
            frame_mainshock,
            from_=1.0,              # Minimum value
            to=10.0,                # Maximum value
            resolution=0.1,         # Step size
            orient="horizontal",    # Horizontal slider
            variable=self.mainshock_mag_var,
            bg="#ffffff",
            highlightthickness=0,
            length=200              # Slider width in pixels
        )
        self.mainshock_slider.pack(side="right", padx=8)

        # ===========================================
        # STATUS LABEL
        # ===========================================
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            fg="#777",
            bg="#f5f5f5",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=(8, 4))

        # ===========================================
        # ACTION BUTTONS
        # ===========================================
        btn_frame = tk.Frame(self.root, bg="#f5f5f5")
        btn_frame.pack(pady=10)

        def modern_btn(parent, text, cmd, bg):
            """Create a styled button."""
            return tk.Button(
                parent,
                text=text,
                command=cmd,
                width=20,
                height=1,
                relief="flat",
                bg=bg,
                fg="black",
                activebackground=bg,
                font=("Segoe UI", 10, "bold"),
            )

        # Background Movement button (green) - no mainshocks
        modern_btn(btn_frame, "Background Movement", self.start_background, "#d7f7d0").grid(row=0, column=0, padx=12)
        
        # Main Shock button (red) - includes mainshocks and aftershocks
        modern_btn(btn_frame, "Main Shock", self.start_mainshock, "#ffd0d0").grid(row=0, column=1)

        # Stop button (blue) - initially disabled
        self.stop_btn = modern_btn(self.root, "Stop Publishing", self.stop_publishing, "#d0e5ff")
        self.stop_btn.config(state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

    # ===========================================
    # BUTTON HANDLERS
    # ===========================================
    def start_background(self):
        """
        Start publishing in Background Movement mode.
        Only generates background noise and foreshocks (no mainshocks).
        """
        self.stop_publishing()
        self.start_publishing(False)  # use_rupture = False

    def start_mainshock(self):
        """
        Start publishing in Main Shock mode.
        Generates mainshocks, aftershocks, and background activity.
        """
        self.stop_publishing()
        self.start_publishing(True)  # use_rupture = True

    # ===========================================
    # PUBLISHING LOGIC
    # ===========================================
    def start_publishing(self, use_rupture):
        """
        Start publishing earthquake data to MQTT.
        
        Args:
            use_rupture: If True, generate mainshocks and aftershocks.
                        If False, only generate background activity.
        """
        # Get topic from dropdown
        topic = self.topic_var.get().strip()

        # ===========================================
        # VALIDATE INPUTS
        # ===========================================
        
        # Validate reading count
        count_text = self.count_entry.get().strip()
        if not count_text.isdigit():
            messagebox.showerror("Error", "Count must be positive integer.")
            return

        # Validate interval
        try:
            interval = float(self.interval_entry.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Interval must be positive number.")
            return

        # Validate skip count
        skip_text = self.skip_entry.get().strip()
        if not skip_text.isdigit():
            messagebox.showerror("Error", "Skip count must be positive integer.")
            return
        self.skip_count = int(skip_text)

        # ===========================================
        # GENERATE SKIP POSITIONS
        # ===========================================
        # Randomly select which readings to skip (simulate missing data)
        self.skip_positions = set(random.sample(range(int(count_text)), k=self.skip_count))
        print("Skip positions:", self.skip_positions)

        # ===========================================
        # CREATE PUBLISHER AND GENERATOR
        # ===========================================
        self.publisher = EarthquakePublisher()
        self.publisher.connect()

        # Create data generator
        # If use_rupture is True, schedule mainshocks on day 0
        mainshock_at_day = 0 if use_rupture else None
        self.publisher.generator = EarthquakeMagnitudeGenerator(
            days_window=7,
            readings_per_day=240,
            mainshock_at_day=mainshock_at_day
        )
        
        # Set mainshock magnitude from slider
        self.publisher.generator.mainshock_magnitude = self.mainshock_mag_var.get()

        # ===========================================
        # GENERATE RANDOM LOCATION
        # ===========================================
        # Each publishing session has a fixed location
        self.cur_lat = round(random.uniform(-90, 90), 4)      # Latitude
        self.cur_long = round(random.uniform(-180, 180), 4)   # Longitude
        self.cur_depth = round(random.uniform(1, 30), 1)      # Depth in km
        self.cur_event = "mainshock" if use_rupture else "background"

        # ===========================================
        # INITIALIZE STATE
        # ===========================================
        self.total_readings = int(count_text)
        self.interval_ms = int(interval * 1000)  # Convert seconds to milliseconds
        self.current_reading = 0
        self.is_publishing = True

        # Store parameters for use in publish_next()
        self.publish_params = dict(
            topic=topic,
            use_background=True,
            use_foreshock=True,
            use_rupture=use_rupture,
            use_aftershock=use_rupture
        )

        # Update UI
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Publishing...", fg="green")

        # Start publishing loop
        self.publish_next()

    def publish_next(self):
        """
        Publish the next reading to MQTT.
        
        This method is called repeatedly using Tkinter's after() method
        to create a timed loop without blocking the GUI.
        """
        # Check if we should stop
        if not self.is_publishing or self.current_reading >= self.total_readings:
            self.finish_publishing()
            return

        try:
            p = self.publish_params
            
            # ===========================================
            # GENERATE MAGNITUDE
            # ===========================================
            if self.current_reading in self.skip_positions:
                # Skip this reading (simulate missing data)
                magnitude = 0.0
            else:
                # Generate magnitude using the generator
                magnitude = self.publisher.generator.generate_magnitude(
                    use_background=p['use_background'],
                    use_foreshock=p['use_foreshock'],
                    use_rupture=p['use_rupture'],
                    use_aftershock=p['use_aftershock'],
                    flag=(self.current_reading % 50) > 24  # Extra noise variation
                )

            # ===========================================
            # CREATE JSON PAYLOAD
            # ===========================================
            payload = json.dumps({
                "id": self.current_reading,
                "location": {
                    "latitude": self.cur_lat,
                    "longitude": self.cur_long,
                    "depth_km": self.cur_depth
                },
                "timestamp": time.asctime(),
                "magnitude": magnitude,
                "event_type": self.cur_event,
            })

            # ===========================================
            # PUBLISH TO MQTT
            # ===========================================
            self.publisher.client.publish(p['topic'], payload)
            print(f"[publish to {p['topic']}] seq={self.current_reading} mag={magnitude}")

            # Update status label
            self.status_label.config(
                text=f"Published {self.current_reading+1}/{self.total_readings}",
                fg="green"
            )

            # Move to next reading
            self.current_reading += 1
            
            # Schedule next publish after interval
            self.root.after(self.interval_ms, self.publish_next)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.finish_publishing()

    # ===========================================
    # STOP AND CLEANUP
    # ===========================================
    def stop_publishing(self):
        """
        Stop publishing (called when user clicks Stop button).
        """
        self.is_publishing = False
        if self.publisher:
            self.publisher.disconnect()
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Publishing stopped", fg="red")

    def finish_publishing(self):
        """
        Called when all readings have been published.
        """
        self.is_publishing = False
        if self.publisher:
            self.publisher.disconnect()
        self.status_label.config(text="Completed", fg="blue")
        self.stop_btn.config(state=tk.DISABLED)


# ===========================================
# MAIN ENTRY POINT
# ===========================================
def main():
    """
    Create and run the publisher GUI.
    """
    root = tk.Tk()
    EarthquakeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

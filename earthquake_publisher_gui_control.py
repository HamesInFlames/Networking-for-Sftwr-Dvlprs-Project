# earthquake_gui.py
import tkinter as tk
import json
import time

from tkinter import messagebox
from earthquake_publisher import EarthquakePublisher


class EarthquakeGUI:
    def __init__(self, root):
        self.root = root
        self.publisher = None
        self.is_publishing = False
        self.current_reading = 0
        self.total_readings = 0
        self.interval_ms = 0
        self.publish_params = {}
        
        self.setup_gui()
    
    def setup_gui(self):
        self.root.title("Earthquake Data Publisher")
        self.root.geometry("420x250")
        
        # Title Heading
        title_label = tk.Label(
            self.root,
            text="Earthquake Data Publisher",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Topic input
        frame_topic = tk.Frame(self.root)
        frame_topic.pack()
        
        tk.Label(frame_topic, text="Topic: ").grid(row=0, column=0, sticky="w")
        self.topic_var = tk.StringVar(value="movement/channel1")
        topic_options = ["movement/channel1", "movement/channel2"]
        topic_menu = tk.OptionMenu(frame_topic, self.topic_var, *topic_options)
        topic_menu.config(width=20)
        topic_menu.grid(row=0, column=1, padx=(6, 0))
        
        # Count input
        frame_count = tk.Frame(self.root)
        frame_count.pack(pady=5)
        
        tk.Label(frame_count, text="Number of readings: ").grid(row=0, column=0)
        self.count_entry = tk.Entry(frame_count, width=10)
        self.count_entry.insert(0, "50")
        self.count_entry.grid(row=0, column=1)
        
        # Interval input
        frame_interval = tk.Frame(self.root)
        frame_interval.pack(pady=5)
        
        tk.Label(frame_interval, text="Interval (seconds): ").grid(row=0, column=0)
        self.interval_entry = tk.Entry(frame_interval, width=10)
        self.interval_entry.insert(0, "1.0")
        self.interval_entry.grid(row=0, column=1)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            font=("Arial", 10),
            fg="gray"
        )
        self.status_label.pack(pady=5)
        
        # Buttons Frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.background_btn = tk.Button(
            button_frame,
            text="Background Movement",
            width=30,
            bg="lightgreen",
            command=self.start_background_mode
        )
        self.background_btn.grid(row=0, column=0, padx=10)
        
        self.mainshock_btn = tk.Button(
            button_frame,
            text="Main Shock",
            width=14,
            bg="lightcoral",
            command=self.start_mainshock_mode
        )
        self.mainshock_btn.grid(row=0, column=1, padx=10)
        
        # Stop button
        self.stop_btn = tk.Button(
            self.root,
            text="Stop Publishing",
            width=20,
            bg="lightblue",
            command=self.stop_publishing,
            state=tk.DISABLED
        )
        self.stop_btn.pack(pady=5)
    
    def start_background_mode(self):
        # Start publisher with background seismic activity only
        self.stop_publishing()  # Stop any existing publishing
        
        self.run_publisher(
            use_background=True,
            use_foreshock=True,
            use_rupture=False,
            use_aftershock=False
        )
    
    def start_mainshock_mode(self):
        # Start publisher with mainshock and aftershock events
        self.stop_publishing()  # Stop any existing publishing
        
        self.run_publisher(
            use_background=True,
            use_foreshock=True,
            use_rupture=True,
            use_aftershock=True
        )
    
    def run_publisher(self, use_background, use_foreshock, use_rupture, use_aftershock):

        # Validate inputs
        topic = self.topic_var.get().strip()
        
        if not topic:
            messagebox.showerror("Error", "Topic cannot be empty.")
            return
        
        count_text = self.count_entry.get().strip()
        if not count_text.isdigit() or int(count_text) <= 0:
            messagebox.showerror("Error", "Number of readings must be a positive integer.")
            return
        
        interval_text = self.interval_entry.get().strip()
        try:
            interval = float(interval_text)
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Interval must be a positive number.")
            return
        
        count = int(count_text)
        self.interval_ms = int(interval * 1000)  # Convert to milliseconds
        
        # Store publishing parameters
        self.publish_params = {
            'topic': topic,
            'use_background': use_background,
            'use_foreshock': use_foreshock,
            'use_rupture': use_rupture,
            'use_aftershock': use_aftershock
        }
        
        # Initialize publisher
        self.publisher = EarthquakePublisher()
        self.publisher.connect()
        
        # Initialize generator
        import random
        mainshock_at_day = 0 if use_rupture else None
        from earthquake_data_generator_event import EarthquakeMagnitudeGenerator
        self.publisher.generator = EarthquakeMagnitudeGenerator(
            days_window=7,
            readings_per_day=240,
            mainshock_at_day=mainshock_at_day
        )
        
        # Generate random location
        self.cur_lat = round(random.uniform(-90, 90), 4)
        self.cur_long = round(random.uniform(-180, 180), 4)
        self.cur_depth = round(random.uniform(1, 30), 1)
        self.cur_event = "mainshock" if use_rupture else "background"
        
        # Reset counters
        self.current_reading = 0
        self.total_readings = count
        self.is_publishing = True
        
        # Disable start buttons, enable stop button
        #self.background_btn.config(state=tk.DISABLED)
        #self.mainshock_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        mode = "Mainshock" if use_rupture else "Background"
        self.status_label.config(text=f"Publishing in {mode} mode...", fg="green")
        
        # Start publishing loop
        self.publish_next_reading()
    
    def publish_next_reading(self):
        # Check if publishing should continue
        if not self.is_publishing or self.current_reading >= self.total_readings:
            self.finish_publishing()
            return
        
        try:
            # Generate magnitude
            magnitude = self.publisher.generator.generate_magnitude(
                use_background=self.publish_params['use_background'],
                use_foreshock=self.publish_params['use_foreshock'],
                use_rupture=self.publish_params['use_rupture'],
                use_aftershock=self.publish_params['use_aftershock'],
                flag=(self.current_reading % 50) > 24
            )
            
            # Create payload
            payload_data = {
                "id": self.current_reading,
                "location": {
                    "latitude": self.cur_lat,
                    "longitude": self.cur_long,
                    "depth_km": self.cur_depth
                },
                "timestamp": time.asctime(),
                "magnitude": magnitude,
                "event_type": self.cur_event,
            }
            
            payload = json.dumps(payload_data)
            
            # Publish to MQTT
            self.publisher.client.publish(self.publish_params['topic'], payload=payload)
            print(f"Published seq={self.current_reading} magnitude={magnitude} event={self.cur_event} to {self.publish_params['topic']}")
            
            # Update status
            self.status_label.config(
                text=f"Published {self.current_reading + 1}/{self.total_readings} readings",
                fg="green"
            )
            
            # Increment counter
            self.current_reading += 1
            
            # Schedule next reading
            self.root.after(self.interval_ms, self.publish_next_reading)
            
        except Exception as e:
            messagebox.showerror("Error", f"Publishing error: {str(e)}")
            self.finish_publishing()
    
    def stop_publishing(self):
        # Stop the current publishing operation
        if self.is_publishing:
            self.is_publishing = False
            if self.publisher:
                self.publisher.disconnect()
            self.status_label.config(text="Publishing stopped", fg="red")
            print("Publishing stopped by user")
        
        self.reset_buttons()
    
    def finish_publishing(self):
        # disconnect from broker
        self.is_publishing = False
        if self.publisher:
            self.publisher.disconnect()
        
        self.status_label.config(
            text=f"Completed: {self.current_reading} readings published",
            fg="blue"
        )
        self.reset_buttons()
    
    def reset_buttons(self):
        # reset buttons
        self.background_btn.config(state=tk.NORMAL)
        self.mainshock_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = EarthquakeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


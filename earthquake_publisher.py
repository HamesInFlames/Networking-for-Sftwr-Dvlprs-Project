# earthquake_publisher.py
import tkinter as tk
from tkinter import messagebox
import json
import random
import time
import paho.mqtt.client as mqtt
from earthquake_data_generator import EarthquakeMagnitudeGenerator


# Publisher
class EarthquakePublisher:
    def __init__(self, broker_host='localhost', broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = None
        self.generator = None

    def connect(self):
        self.client = mqtt.Client()
        self.client.connect(self.broker_host, self.broker_port)
        self.client.loop_start()
        print(f"[Publisher] Connected to {self.broker_host}:{self.broker_port}")

    def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("[Publisher] Disconnected")

# Publisher GUI
class EarthquakeGUI:
    def __init__(self, root):
        self.root = root
        self.publisher = None
        self.is_publishing = False
        self.current_reading = 0
        self.total_readings = 0
        self.interval_ms = 0
        self.publish_params = {}
        # array of randomly generated skip positions between 0 and count.entry
        self.skip_count = 3
        self.skip_positions = set()

        self.setup_gui()

    #  GUI SETUP 
    def setup_gui(self):
        self.root.title("Earthquake Data Publisher")
        self.root.geometry("460x500")
        self.root.configure(bg="#f5f5f5")

        title = tk.Label(
            self.root,
            text="Earthquake Data Publisher",
            font=("Segoe UI", 18, "bold"),
            bg="#f5f5f5",
            fg="#333",
        )
        title.pack(pady=(15, 10))

        # ---------- Utility function to create modern frames ----------
        def modern_frame(parent):
            return tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", padx=10, pady=10)

        # Topic Selection Frame 

        frame_topic = modern_frame(self.root)
        frame_topic.pack(pady=5, fill="x", padx=15)

        frame_topic.columnconfigure(0, weight=0)   # label column (fixed)
        frame_topic.columnconfigure(1, weight=1)   # dropdown column (expands)

        tk.Label(frame_topic, text="Topic:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self.topic_var = tk.StringVar(value="movement/California")

        def on_topic_change(selected_topic):
            self.stop_publishing()  # Stop current publishing if any
            self.topic_var.set(selected_topic)  # Update the variable

        topic_menu = tk.OptionMenu(frame_topic, self.topic_var, "movement/BritishColumbia", "movement/California", "movement/Tokyo",
                                   command=on_topic_change)
        topic_menu.config(width=25, bg="#fafafa", relief="flat")
        topic_menu.grid(row=0, column=1, padx=8, sticky="e") 

        # Readings count
        frame_count = modern_frame(self.root)
        frame_count.pack(pady=5, fill="x", padx=15)

        frame_count.columnconfigure(0, weight=0)
        frame_count.columnconfigure(1, weight=1)

        tk.Label(frame_count, text="Number of readings:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0)
        self.count_entry = tk.Entry(frame_count, width=12, relief="flat", highlightthickness=1, highlightbackground="#ccc")
        self.count_entry.insert(0, "100")
        self.count_entry.grid(row=0, column=1, padx=8, sticky="e")

        # Interval
        frame_interval = modern_frame(self.root)
        frame_interval.pack(pady=5, fill="x", padx=15)

        frame_interval.columnconfigure(0, weight=0)
        frame_interval.columnconfigure(1, weight=1)

        tk.Label(frame_interval, text="Interval (seconds):", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0)
        self.interval_entry = tk.Entry(frame_interval, width=12, relief="flat", highlightthickness=1, highlightbackground="#ccc")
        self.interval_entry.insert(0, "0.5")
        self.interval_entry.grid(row=0, column=1, padx=8, sticky="e")

        # No. of readings to skip
        frame_skip = modern_frame(self.root)
        frame_skip.pack(pady=5, fill="x", padx=15)

        frame_skip.columnconfigure(0, weight=0)
        frame_skip.columnconfigure(1, weight=1)

        tk.Label(frame_skip, text="Number of readings to skip:", bg="#ffffff", font=("Segoe UI", 10)).grid(row=0, column=0)
        self.skip_entry = tk.Entry(frame_skip, width=12, relief="flat", highlightthickness=1, highlightbackground="#ccc")
        self.skip_entry.insert(0, "3")
        self.skip_entry.grid(row=0, column=1, padx=8, sticky="e")

        # Status
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            fg="#777",
            bg="#f5f5f5",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=(8, 4))

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#f5f5f5")
        btn_frame.pack(pady=10)

        def modern_btn(parent, text, cmd, bg):
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

        modern_btn(btn_frame, "Background Movement", self.start_background, "#d7f7d0").grid(row=0, column=0, padx=12)
        modern_btn(btn_frame, "Main Shock", self.start_mainshock, "#ffd0d0").grid(row=0, column=1)

        self.stop_btn = modern_btn(self.root, "Stop Publishing", self.stop_publishing, "#d0e5ff")
        self.stop_btn.config(state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

    # Background/ Mainshock button handlers
    def start_background(self):
        self.stop_publishing()
        self.start_publishing(False)

    def start_mainshock(self):
        self.stop_publishing()
        self.start_publishing(True)

    # Publish
    def start_publishing(self, use_rupture):
        topic = self.topic_var.get().strip()

        # Validate count
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

        # Generate n (skip_count) skip positions
        self.skip_positions = set(random.sample(range(int(count_text)), k=self.skip_count))
        print("!!!!GUI!!! Skip positions:", self.skip_positions)

        # Create publisher
        self.publisher = EarthquakePublisher()
        self.publisher.connect()

        # Generator
        mainshock_at_day = 0 if use_rupture else None
        self.publisher.generator = EarthquakeMagnitudeGenerator(
            days_window=7,
            readings_per_day=240,
            mainshock_at_day=mainshock_at_day
        )

        # Random location
        self.cur_lat = round(random.uniform(-90, 90), 4)
        self.cur_long = round(random.uniform(-180, 180), 4)
        self.cur_depth = round(random.uniform(1, 30), 1)
        self.cur_event = "mainshock" if use_rupture else "background"

        # State
        self.total_readings = int(count_text)
        self.interval_ms = int(interval * 1000)
        self.current_reading = 0
        self.is_publishing = True

        self.publish_params = dict(
            topic=topic,
            use_background=True,
            use_foreshock=True,
            use_rupture=use_rupture,
            use_aftershock=use_rupture
        )

        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Publishing...", fg="green")

        self.publish_next()

    # Publish next reading
    def publish_next(self):
        if not self.is_publishing or self.current_reading >= self.total_readings:
            self.finish_publishing()
            return

        try:
            p = self.publish_params
            if self.current_reading in self.skip_positions:
                magnitude = 0.0
            else:
                magnitude = self.publisher.generator.generate_magnitude(
                    use_background=p['use_background'],
                    use_foreshock=p['use_foreshock'],
                    use_rupture=p['use_rupture'],
                    use_aftershock=p['use_aftershock'],
                    flag=(self.current_reading % 50) > 24
                )

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

            self.publisher.client.publish(p['topic'], payload)
            print(f"[publish to {p['topic']}] seq={self.current_reading} mag={magnitude}")

            self.status_label.config(
                text=f"Published {self.current_reading+1}/{self.total_readings}",
                fg="green"
            )

            self.current_reading += 1
            self.root.after(self.interval_ms, self.publish_next)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.finish_publishing()

    # Stop & Cleanup
    def stop_publishing(self):
        self.is_publishing = False
        if self.publisher:
            self.publisher.disconnect()
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Publishing stopped", fg="red")

    def finish_publishing(self):
        self.is_publishing = False
        if self.publisher:
            self.publisher.disconnect()
        self.status_label.config(text="Completed", fg="blue")
        self.stop_btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    EarthquakeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

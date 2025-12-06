import tkinter as tk
from tkinter import ttk

class DynamicLineChart:
    def __init__(self, master, max_points=50):
        self.master = master
        self.max_points = max_points
        self.values = [0.0] * max_points  # initial values
        self.canvas_w = 700
        self.canvas_h = 320

        self.initUI()
    
    def initUI(self):
        self.master.title("Earthquake Magnitude - Dynamic Line Chart")
        '''        
        top_frame = ttk.Frame(self.master)
        top_frame.pack(side="top", fill="x", padx=8, pady=8)
        ttk.Label(top_frame, text="Dynamic Earthquake Magnitude").pack(side="left")
        '''        
        self.canvas = tk.Canvas(self.master, width=self.canvas_w, height=self.canvas_h, bg="white")
        self.canvas.pack(padx=8, pady=(0,8))
        
        self.draw_line()

    def add_value(self, val):
        """Add a new magnitude value and redraw chart"""
        if len(self.values) >= self.max_points:
            self.values.pop(0)
        self.values.append(val)
        self.master.after(0, self.draw_line)

    def clear(self):
        # Clear all stored values
        self.values = [0.0] * self.max_points

    def draw_line(self):
        self.canvas.delete("all")
        if not self.values:
            return
        
        pad_x = 50
        pad_y = 30
        left, right = pad_x, self.canvas_w - pad_x
        top, bottom = pad_y, self.canvas_h - pad_y

#        min_val = min(self.values)
#        max_val = max(self.values)
        min_val = 0
        max_val = 9
        if max_val == min_val:
            max_val += 1

        # horizontal grid lines
        for i in range(5):
            y = top + i * (bottom - top) / 4
            self.canvas.create_line(left, y, right, y, fill="#eee")
            tick_val = max_val - (i * (max_val - min_val) / 4)
            self.canvas.create_text(left-8, y, text=f"{tick_val:.2f}", anchor="e", font=("Arial", 8))

        n = len(self.values)
        plot_w = right - left
        x_step = plot_w / (n - 1) if n > 1 else plot_w

        points = []
        for i, v in enumerate(self.values):
            x = left + i * x_step
            y = bottom - (v - min_val) / (max_val - min_val) * (bottom - top)
            points.append((x, y))

        flat_points = [coord for point in points for coord in point]
        if len(flat_points) >= 4:
            self.canvas.create_line(*flat_points, fill="#ff6600", width=2)

#        for x, y in points:
#            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="#ff6600", outline="")

        # --- Time-based X-axis labels over last 2 hours ---
        total_minutes = 120  # 2 hours
        label_times = [0, 15, 30, 45, 60, 75, 90, 105, 120]  # minutes from left to right
        #label_times = [120, 105, 90, 75, 60, 45, 30, 15, 0]  # minutes from left to right

        for minutes in label_times:
            fraction = minutes / total_minutes
            x = left + fraction * (right - left)

            if minutes == 120:
                label = "Now"
            else:
                #hrs = -(minutes // 60)
                hrs = -((120-minutes) // 60)
                mins = minutes % 60
                label = f"{hrs}:{mins:02d}"

            self.canvas.create_text(x, bottom + 12, text=label, anchor="n", font=("Arial", 8))

        # X-axis line
        self.canvas.create_line(left, bottom, right, bottom, fill="black")


        # Title
        self.canvas.create_text(self.canvas_w/2, 12, text="Earthquake Magnitude", font=("Arial", 12, "bold"))

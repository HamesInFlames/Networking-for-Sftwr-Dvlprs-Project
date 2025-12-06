"""
Dynamic Line Chart Module for Earthquake Magnitude Visualization

This module provides a real-time updating line chart using Tkinter Canvas.
It displays earthquake magnitude readings over time with automatic scaling
and timestamp tracking.

Author: Group Assignment - COMP216
Date: Fall 2025
"""

import tkinter as tk
from datetime import datetime


class DynamicLineChart:
    """
    A resizable line chart widget that displays real-time earthquake magnitude data.
    
    Features:
    - Y-axis: Fixed scale from 0 to 10 (earthquake magnitude)
    - X-axis: Timestamps showing when each reading was received
    - Auto-scrolling: Old data points are removed as new ones arrive
    - Resizable: Chart scales with window size
    """
    
    def __init__(self, master, max_points=100):
        """
        Initialize the chart.
        
        Args:
            master: Parent Tkinter widget (usually root window)
            max_points: Maximum number of data points to display (default: 100)
        """
        self.master = master
        self.max_points = max_points
        
        # Data storage - parallel arrays for values and their timestamps
        self.values = [0.0] * max_points      # Magnitude values (0.0 to 10.0)
        self.timestamps = [None] * max_points  # When each value was received
        
        # Y-axis bounds (earthquake magnitude scale)
        self.min_val = 0   # Minimum magnitude
        self.max_val = 10  # Maximum magnitude
        
        # Build the UI
        self.initUI()
    
    def initUI(self):
        """
        Set up the user interface components.
        Creates the main window and canvas for drawing.
        """
        # Window title and size
        self.master.title("Earthquake Magnitude Monitor")
        self.master.geometry("800x400")  # Default window size
        
        # Create canvas widget for drawing the chart
        # bg="white" sets background color
        self.canvas = tk.Canvas(self.master, bg="white")
        # fill="both" makes canvas expand in both directions
        # expand=True allows canvas to grow with window
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bind the Configure event to handle window resizing
        # When window is resized, on_resize() is called
        self.canvas.bind("<Configure>", self.on_resize)
        
        # Draw initial empty chart
        self.draw_line()

    def on_resize(self, event):
        """
        Handle window resize events.
        Redraws the chart to fit the new window size.
        
        Args:
            event: Tkinter event object containing new size info
        """
        self.draw_line()

    def add_value(self, val):
        """
        Add a new magnitude reading to the chart.
        
        This method:
        1. Removes the oldest value if at max capacity
        2. Adds the new value with current timestamp
        3. Triggers a redraw of the chart
        
        Args:
            val: New magnitude value (float, 0.0 to 10.0)
        """
        # Remove oldest data point if we're at capacity
        if len(self.values) >= self.max_points:
            self.values.pop(0)       # Remove oldest value
            self.timestamps.pop(0)   # Remove oldest timestamp
        
        # Add new data point
        self.values.append(val)
        self.timestamps.append(datetime.now())  # Record current time
        
        # Schedule a redraw (after(0, ...) runs on next event loop iteration)
        self.master.after(0, self.draw_line)

    def clear(self):
        """
        Clear all data from the chart.
        Resets values and timestamps to initial empty state.
        Called when switching topics/regions.
        """
        self.values = [0.0] * self.max_points
        self.timestamps = [None] * self.max_points
        self.draw_line()

    def draw_line(self):
        """
        Main drawing method - renders the entire chart.
        
        This method:
        1. Clears the canvas
        2. Calculates plot area dimensions
        3. Draws title, grid, axes, labels
        4. Plots the data line
        5. Shows current value indicator
        """
        # Clear all existing drawings
        self.canvas.delete("all")
        
        # Get current canvas dimensions
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Don't draw if canvas is too small (avoids errors during initialization)
        if canvas_w < 100 or canvas_h < 100:
            return
        
        # ===========================================
        # CALCULATE PLOT AREA
        # ===========================================
        # Padding creates space for axis labels
        pad_left = 50    # Space for Y-axis labels
        pad_right = 20   # Small right margin
        pad_top = 30     # Space for title
        pad_bottom = 50  # Space for X-axis labels
        
        # Define plot boundaries
        left = pad_left
        right = canvas_w - pad_right
        top = pad_top
        bottom = canvas_h - pad_bottom
        
        # Calculate actual plot dimensions
        plot_width = right - left
        plot_height = bottom - top
        
        # ===========================================
        # DRAW TITLE
        # ===========================================
        self.canvas.create_text(
            canvas_w / 2, 15,  # Centered at top
            text="Earthquake Magnitude",
            font=("Arial", 12, "bold")
        )
        
        # ===========================================
        # DRAW Y-AXIS GRID LINES AND LABELS
        # ===========================================
        # Draw 11 horizontal lines (for values 0 through 10)
        for i in range(11):
            # Calculate Y position for this value
            # i=0 is at bottom (magnitude 0), i=10 is at top (magnitude 10)
            y = bottom - (i / 10) * plot_height
            
            # Draw light gray grid line
            self.canvas.create_line(left, y, right, y, fill="#ddd")
            
            # Draw Y-axis label (magnitude value)
            self.canvas.create_text(
                left - 10, y,      # Position to left of axis
                text=str(i),       # The magnitude value
                font=("Arial", 9),
                anchor="e"         # Right-align text
            )
        
        # ===========================================
        # DRAW X-AXIS TIME LABELS
        # ===========================================
        num_labels = 5  # Number of time labels to show
        for i in range(num_labels + 1):
            # Calculate X position for this label
            x = left + (i / num_labels) * plot_width
            
            # Draw tick mark
            self.canvas.create_line(x, bottom, x, bottom + 5, fill="black")
            
            # Get timestamp for this position in the data array
            idx = int((i / num_labels) * (len(self.timestamps) - 1))
            
            # Format timestamp or show placeholder
            if idx < len(self.timestamps) and self.timestamps[idx]:
                time_str = self.timestamps[idx].strftime("%H:%M:%S")
            else:
                time_str = "--:--:--"  # No data yet
            
            # Draw time label
            self.canvas.create_text(x, bottom + 20, text=time_str, font=("Arial", 8))
        
        # ===========================================
        # DRAW AXES LINES
        # ===========================================
        # Y-axis (vertical line on left)
        self.canvas.create_line(left, top, left, bottom, fill="black", width=2)
        
        # X-axis (horizontal line at bottom)
        self.canvas.create_line(left, bottom, right, bottom, fill="black", width=2)
        
        # ===========================================
        # DRAW AXIS LABELS
        # ===========================================
        # Y-axis label (rotated 90 degrees)
        self.canvas.create_text(
            20, (top + bottom) / 2,  # Centered vertically on left edge
            text="Mag",
            font=("Arial", 9),
            angle=90  # Rotate text vertically
        )
        
        # X-axis label
        self.canvas.create_text(
            (left + right) / 2, canvas_h - 5,  # Centered at bottom
            text="Time",
            font=("Arial", 9)
        )
        
        # ===========================================
        # DRAW DATA LINE
        # ===========================================
        # Skip if no data
        if not self.values:
            return
        
        n = len(self.values)
        
        # Calculate horizontal spacing between points
        x_step = plot_width / (n - 1) if n > 1 else plot_width
        
        # Convert data values to canvas coordinates
        points = []
        for i, v in enumerate(self.values):
            # X coordinate: spread points evenly across plot width
            x = left + i * x_step
            
            # Clamp value to valid range (0-10)
            v_clamped = max(self.min_val, min(self.max_val, v))
            
            # Y coordinate: map value to plot height
            # Note: Canvas Y increases downward, so we subtract from bottom
            y = bottom - (v_clamped / self.max_val) * plot_height
            
            points.append((x, y))
        
        # Flatten points list for create_line(): [(x1,y1), (x2,y2)] -> [x1, y1, x2, y2]
        flat_points = [coord for point in points for coord in point]
        
        # Draw the line (need at least 2 points = 4 coordinates)
        if len(flat_points) >= 4:
            self.canvas.create_line(
                *flat_points,     # Unpack all coordinates
                fill="red",       # Line color
                width=2           # Line thickness
            )
        
        # ===========================================
        # DRAW CURRENT VALUE INDICATOR
        # ===========================================
        # Show the most recent value and timestamp in top-right corner
        if self.values and self.timestamps[-1]:
            current = self.values[-1]
            current_time = self.timestamps[-1].strftime("%H:%M:%S")
            
            # Current magnitude value
            self.canvas.create_text(
                right - 60, top + 10,
                text=f"Current: {current:.1f}",
                font=("Arial", 10, "bold"),
                fill="red"
            )
            
            # Current timestamp
            self.canvas.create_text(
                right - 60, top + 25,
                text=f"Time: {current_time}",
                font=("Arial", 9),
                fill="black"
            )

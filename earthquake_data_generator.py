"""
Earthquake Magnitude Generator Module

Generates realistic earthquake magnitude readings with:
- Low background seismic noise (0.5-1.5 magnitude)
- Sharp mainshock spikes (using slider value or random 6-10)
- Decaying aftershocks following Omori's law

Omori's Law: Aftershocks decrease in frequency and magnitude over time.
The first aftershocks are strongest, then they gradually weaken.

Author: Group Assignment - COMP216
Date: Fall 2025
"""

import math
import random


class EarthquakeMagnitudeGenerator:
    """
    Generates realistic earthquake magnitude data.
    
    The generator produces different types of seismic activity:
    1. Background noise: Small constant tremors (0.3-0.8 magnitude)
    2. Foreshocks: Occasional small bumps before main event
    3. Mainshocks: Large magnitude spikes (controlled by slider)
    4. Aftershocks: Decaying series of smaller quakes after mainshock
    """
    
    def __init__(
        self,
        days_window=30,
        readings_per_day=4,
        aftershock_count_range=(5, 10),
        mainshock_at_day=None
    ):
        """
        Initialize the earthquake generator.
        
        Args:
            days_window: Number of simulated days (affects total readings)
            readings_per_day: How many readings per simulated day
            aftershock_count_range: Min and max number of aftershocks (tuple)
            mainshock_at_day: Which day to schedule mainshocks (None = no schedule)
        """
        # ===========================================
        # SIMULATION PARAMETERS
        # ===========================================
        self.days_window = days_window
        self.readings_per_day = readings_per_day

        # ===========================================
        # MAGNITUDE BOUNDS
        # ===========================================
        self.min_mag = 0.0   # Minimum possible magnitude
        self.max_mag = 10.0  # Maximum possible magnitude (matches Y-axis)

        # ===========================================
        # EARTHQUAKE BEHAVIOR SETTINGS
        # ===========================================
        self.foreshock_prob = 0.03  # 3% chance of foreshock per reading

        # Aftershock parameters
        self.aftershock_count_range = aftershock_count_range

        # ===========================================
        # INTERNAL TIME TRACKING
        # ===========================================
        self._time = 0  # Current time step (increments with each reading)
        self._total_steps = days_window * readings_per_day

        # ===========================================
        # EVENT RECORDS
        # ===========================================
        self._mainshocks = []               # List of mainshock events {time, mag}
        self._scheduled_rupture_steps = []  # Time steps when mainshocks should occur

        # ===========================================
        # AFTERSHOCK TRACKING
        # ===========================================
        # List of scheduled aftershocks: {step: when, magnitude: how strong}
        self._aftershock_schedule = []
        
        # Track the most recent mainshock for aftershock calculations
        self._last_mainshock_time = None
        self._last_mainshock_mag = None
        
        # ===========================================
        # MANUAL TRIGGER SUPPORT (for GUI)
        # ===========================================
        self._pending_manual_mainshock = None  # Pending manual trigger
        self._current_location = None          # Location data
        
        # GUI slider magnitude - if set, use this value for mainshocks
        self.mainshock_magnitude = None

        # ===========================================
        # SCHEDULE INITIAL MAINSHOCKS
        # ===========================================
        # If mainshock_at_day is specified, schedule some mainshocks
        if mainshock_at_day is not None:
            self.schedule_rupture_at_day(mainshock_at_day, num_spikes=3)

    def trigger_manual_mainshock(self, magnitude, location=None):
        """
        Manually trigger a mainshock from the GUI.
        
        Args:
            magnitude: Desired magnitude (0-10)
            location: Optional location data dictionary
            
        Returns:
            bool: True if valid magnitude, False otherwise
        """
        # Validate magnitude is in range
        if magnitude < self.min_mag or magnitude > self.max_mag:
            return False
        
        # Store the pending trigger
        self._pending_manual_mainshock = {
            'magnitude': magnitude,
            'location': location
        }
        self._current_location = location
        return True
    
    def schedule_rupture_at_day(self, day_index, num_spikes=3):
        """
        Schedule mainshocks to occur on a specific day.
        
        Args:
            day_index: Which day (0-based) to schedule mainshocks
            num_spikes: How many mainshock events to schedule
        """
        if 0 <= day_index < self.days_window:
            # Calculate time step range for this day
            first_step = day_index * self.readings_per_day
            last_step = first_step + 30  # Spread over 30 readings
            
            # Schedule random spikes within this range
            for _ in range(num_spikes):
                self._scheduled_rupture_steps.append(
                    random.randint(first_step, last_step)
                )
        
        # Sort for efficient checking
        self._scheduled_rupture_steps.sort()

    def _background_base(self):
        """
        Generate low background seismic noise.
        
        Real seismographs show constant micro-tremors even when
        there's no earthquake activity. This simulates that.
        
        Returns:
            float: Small magnitude value (0.2 to 0.8)
        """
        base = 0.5  # Center value
        noise = random.uniform(-0.3, 0.3)  # Random variation
        return base + noise

    def _maybe_foreshock_offset(self):
        """
        Occasionally generate a small foreshock.
        
        Foreshocks are small tremors that sometimes precede
        larger earthquakes. 3% chance per reading.
        
        Returns:
            float: Foreshock magnitude (0 to 1.5)
        """
        if random.random() < self.foreshock_prob:
            # Foreshock occurred - return medium bump
            return random.uniform(0.5, 1.5)
        # No foreshock - return tiny variation
        return random.uniform(0.0, 0.3)

    def _trigger_rupture(self):
        """
        Check if a mainshock should occur at this time step.
        
        A mainshock triggers if:
        1. There's a pending manual trigger from the GUI, OR
        2. This time step is in the scheduled rupture list
        
        Returns:
            bool: True if mainshock should occur
        """
        # Check for GUI-triggered earthquake
        if self._pending_manual_mainshock is not None:
            return True
        
        # Check for scheduled ruptures
        if self._time in self._scheduled_rupture_steps:
            return True
        
        return False

    def _schedule_aftershocks(self, mainshock_mag):
        """
        Schedule realistic aftershocks following Omori's law.
        
        Omori's Law states that aftershocks:
        - Are most frequent immediately after the mainshock
        - Decrease in frequency over time
        - Decrease in magnitude over time
        
        Args:
            mainshock_mag: Magnitude of the mainshock that just occurred
        """
        # Record mainshock details for decay calculations
        self._last_mainshock_time = self._time
        self._last_mainshock_mag = mainshock_mag
        
        # Determine number of aftershocks (more for bigger quakes)
        num_aftershocks = random.randint(*self.aftershock_count_range)
        
        # Clear old schedule
        self._aftershock_schedule = []
        
        for i in range(num_aftershocks):
            # ===========================================
            # TIMING: Exponential spacing (Omori's law)
            # ===========================================
            # First aftershocks come quickly, later ones spread out
            # Formula: delay = (i+1)^1.5 * 2
            # i=0: delay=2, i=1: delay=6, i=2: delay=10, i=3: delay=16, etc.
            delay = int((i + 1) ** 1.5 * 2)
            aftershock_step = self._time + delay + random.randint(1, 5)
            
            # ===========================================
            # MAGNITUDE: Decay with each aftershock
            # ===========================================
            # First aftershock: ~70% of mainshock
            # Each subsequent: ~85% of previous
            decay_factor = 0.7 * (0.85 ** i)
            aftershock_mag = mainshock_mag * decay_factor
            
            # Add some randomness
            aftershock_mag *= random.uniform(0.8, 1.1)
            
            # Minimum aftershock magnitude (below this is just noise)
            aftershock_mag = max(1.5, aftershock_mag)
            
            # Add to schedule
            self._aftershock_schedule.append({
                'step': aftershock_step,
                'magnitude': aftershock_mag
            })

    def _get_aftershock_magnitude(self):
        """
        Check if an aftershock is scheduled for current time step.
        
        Returns:
            float: Aftershock magnitude if scheduled, 0 otherwise
        """
        for aftershock in self._aftershock_schedule:
            if aftershock['step'] == self._time:
                return aftershock['magnitude']
        return 0

    def generate_magnitude(
        self,
        use_background=True,
        use_foreshock=True,
        use_rupture=True,
        use_aftershock=True,
        flag=False
    ):
        """
        Generate a single magnitude reading.
        
        This is the main method called for each data point.
        It combines all earthquake phenomena into one value.
        
        Args:
            use_background: Include background noise (default: True)
            use_foreshock: Include random foreshocks (default: True)
            use_rupture: Allow mainshock triggers (default: True)
            use_aftershock: Generate aftershocks (default: True)
            flag: Add extra noise variation (default: False)
            
        Returns:
            float: Generated magnitude value (0.0 to 10.0)
        """
        val = 0.0

        # ===========================================
        # 1. BACKGROUND NOISE
        # ===========================================
        # Small constant micro-tremors (0.2 to 0.8)
        if use_background:
            val += self._background_base()

        # ===========================================
        # 2. FORESHOCK
        # ===========================================
        # 3% chance of small bump before main event
        if use_foreshock:
            val += self._maybe_foreshock_offset()

        # ===========================================
        # 3. MAINSHOCK
        # ===========================================
        # Check if a mainshock should occur now
        if use_rupture and self._trigger_rupture():
            # Determine mainshock magnitude
            if self._pending_manual_mainshock is not None:
                # Use manually triggered value
                mainshock_mag = self._pending_manual_mainshock['magnitude']
                self._pending_manual_mainshock = None  # Clear the trigger
            elif self.mainshock_magnitude is not None:
                # Use GUI slider value
                mainshock_mag = self.mainshock_magnitude
            else:
                # Use random value
                mainshock_mag = random.uniform(6.0, self.max_mag)
            
            # Record the mainshock
            self._mainshocks.append({"time": self._time, "mag": mainshock_mag})
            
            # Schedule aftershocks
            self._schedule_aftershocks(mainshock_mag)
            
            # Set output to mainshock magnitude (sharp spike)
            val = mainshock_mag + random.uniform(-0.2, 0.2)

        # ===========================================
        # 4. AFTERSHOCK
        # ===========================================
        # Check if an aftershock is scheduled for this time
        elif use_aftershock:
            aftershock_mag = self._get_aftershock_magnitude()
            if aftershock_mag > 0:
                # Replace background with aftershock value
                val = aftershock_mag + random.uniform(-0.1, 0.1)

        # ===========================================
        # 5. EXTRA NOISE (optional)
        # ===========================================
        if flag:
            val += random.uniform(-0.1, 0.1)

        # ===========================================
        # FINALIZE
        # ===========================================
        # Clamp to valid range (0 to 10)
        val = max(self.min_mag, min(self.max_mag, val))
        
        # Advance time
        self._time += 1
        
        # Return rounded value
        return round(val, 2)
    
    def get_current_location(self):
        """
        Get the current earthquake location data.
        
        Returns:
            dict: Location data or None
        """
        return self._current_location


# ===========================================
# TEST DRIVER
# ===========================================
if __name__ == "__main__":
    """
    Test the generator by printing sample readings.
    Run this file directly to see output.
    """
    # Create generator with 7 day window, 240 readings per day
    gen = EarthquakeMagnitudeGenerator(days_window=7, readings_per_day=240)
    
    # Schedule mainshocks on day 0
    gen.schedule_rupture_at_day(0, num_spikes=3)

    print("Generating earthquake magnitude readings...")
    print("=" * 60)
    
    # Generate and print 100 readings
    for i in range(100):
        magnitude = gen.generate_magnitude(
            use_background=True,
            use_foreshock=True,
            use_rupture=True,
            use_aftershock=True,
            flag=False
        )
        print(f"Step {i}: Magnitude = {magnitude}")
    
    print("=" * 60)

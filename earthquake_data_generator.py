import math
import random
import matplotlib.pyplot as plt

class EarthquakeMagnitudeGenerator:

    def __init__(
        self,
        days_window=30,
        readings_per_day=4,
        aftershock_count_range=(1, 4),  # random 1–4 aftershocks
        mainshock_at_day=None
    ):
        # Input parameters
        self.days_window = days_window
        self.readings_per_day = readings_per_day

        # Internal parameters
        self.min_background = 0.0   # background min & max
        self.max_background = 1.8
        self.min_mag = 0.0          # main shock min & max
        self.max_mag = 8.5
        self.noise_level = 0.1

        # Earthquake behavior settings
        self.foreshock_prob = 0.02
        self.rupture_prob_per_step = 0.001

        # Aftershock parameters
        self.aftershock_count_range = aftershock_count_range
        self.aftershock_c = 0.5
        self.aftershock_decay_p = 1.1

        # Internal time counters
        self._time = 0
        self._total_steps = days_window * readings_per_day

        # Records
        self._mainshocks = []
        self._scheduled_rupture_steps = []

        # Aftershock schedule
        self._aftershock_steps = []

        if mainshock_at_day is not None:
            self.schedule_rupture_at_day(mainshock_at_day, num_spikes=40)

    # Schedule mainshock spikes
    def schedule_rupture_at_day(self, day_index, num_spikes=0):
        print("Before scheduling:", self._scheduled_rupture_steps)
        if 0 <= day_index < self.days_window:
            first_step = day_index * self.readings_per_day
            last_step = first_step + self.readings_per_day - 1
            last_step = first_step + 60
            for _ in range(num_spikes):
                self._scheduled_rupture_steps.append(
                    random.randint(first_step, last_step)
                )
        print(f"Scheduled ruptures at steps: {self._scheduled_rupture_steps}")
        self._scheduled_rupture_steps.sort()

    # Background movement
    def _background_base(self):
        t_days = (self._time / self.readings_per_day) % self.days_window
#        return 0.8 + 0.4 * math.sin((2 * math.pi / self.days_window) * t_days)
#        return 1.2 + 0.8 * math.sin((2 * math.pi / self.days_window) * t_days) * self.noise_level
        return self.max_background + self.min_background * math.sin((2 * math.pi / self.days_window) * t_days) * self.noise_level

    # Foreshock offset
    def _maybe_foreshock_offset(self):
        if random.random() < self.foreshock_prob:
            return random.uniform(0.2, 1.0)
        return random.uniform(0.0, 1.8)

    # Mainshock trigger
    def _trigger_rupture(self):
        if self._time in self._scheduled_rupture_steps:
            return True
    #    return random.random() < self.rupture_prob_per_step

    # Aftershock (4-5)
    def _aftershock_pulse_multi(self, current_step):
        print(f"Generating aftershock at step {current_step} ({(1 - (current_step/self._total_steps)):.2f} decay)")
        return round(random.uniform(5.0, 6.0), 2) * (1 - (current_step/self._total_steps))

    # Main magnitude generator WITH SWITCHES
    def generate_magnitude(
        self,
        use_background=True,
        use_foreshock=True,
        use_rupture=True,
        use_aftershock=True,
        flag=False
    ):

        val = 0.0

        # 1. Background movement
        if use_background:
            val += self._background_base()

        # 2. Foreshock
        if use_foreshock:
            val += self._maybe_foreshock_offset()

        # 3. Mainshock
        mainshock_mag = 0
        if use_rupture and self._trigger_rupture():
#            mainshock_mag = random.uniform(5.8, min(8.5, self.max_mag))
            mainshock_mag = random.uniform(self.min_mag, self.max_mag)
            self._mainshocks.append({"time": self._time, "mag": mainshock_mag})

            # schedule aftershocks for the next day
            next_day_start = ((self._time // self.readings_per_day) + 1) * self.readings_per_day
            num_aftershocks = random.randint(*self.aftershock_count_range)
            self._aftershock_steps = random.sample(
                range(next_day_start, next_day_start + self.readings_per_day),
                k=num_aftershocks
            )

            val += mainshock_mag + random.uniform(-0.1, 0.1)

        # 4. Aftershock
        if use_aftershock:
            if self._time in self._aftershock_steps:
                #print(f"Aftershock triggered at step {self._time}")
                val += self._aftershock_pulse_multi(self._time)


        # 5. Extra noise (optional)
        if flag:
            val += random.uniform(-0.2, 0.2)

        # finalize
        val = max(self.min_mag, min(self.max_mag, val))
        self._time += 1
        return round(val, 2)



if __name__ == "__main__":
    gen = EarthquakeMagnitudeGenerator(days_window=7, readings_per_day=240)

    # Day 2 has a mainshock cluster
    gen.schedule_rupture_at_day(0, num_spikes=20)

    total_steps = gen.days_window * gen.readings_per_day
    times = [i / gen.readings_per_day for i in range(total_steps)]

    magnitudes = [
        gen.generate_magnitude(
            use_background=True,
            use_foreshock=True,
            use_rupture=True,
            use_aftershock=True,
            flag=False
        )
        for _ in range(total_steps)
    ]

    plt.figure(figsize=(12, 5))
    plt.plot(times, magnitudes, "m")
    plt.title("Earthquake Simulation")
    plt.xlabel("Day")
    plt.ylabel("Magnitude (Mw)")
    plt.grid(True)
    plt.show()

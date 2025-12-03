import math
import random
import matplotlib.pyplot as plt

class CO2DataGenerator:
    def __init__(self, min_ppm=400, max_ppm=1500, noise_level=0.2, peak_hours=(8, 17), readings_per_hour=2):
        self.min_ppm = min_ppm
        self.max_ppm = max_ppm
        self.noise_level = noise_level
        self.peak_hours = peak_hours
        self.readings_per_hour = readings_per_hour
        self._time = 0

    def _generate_normalized_value(self, flag=False):
        """
        Private helper method that returns a normalized CO₂ level (0–1)
        based on the time of day, traffic patterns, and randomness.
        """
        hour = (self._time / self.readings_per_hour) % 24

        base_pattern = 0.6 * math.sin((math.pi / 12) * hour - math.pi / 2) + 0.6

        # Morning peak: roughly 8–10 AM (rush hour)
        if self.peak_hours[0] <= hour <= self.peak_hours[0] + 2:
            base_pattern += 0.25  # boost levels during morning traffic

        # Midday valley: lower CO₂ between 11 AM – 3 PM (less traffic)
        elif 11 <= hour <= 15:
            base_pattern -= 0.3  # dip levels during midday

        # Evening peak: roughly 5–7 PM (evening rush)
        elif self.peak_hours[1] <= hour <= self.peak_hours[1] + 2:
            base_pattern += 0.25  # boost levels again

        # If irregularity flag is set, add an extra random spike (simulating unusual traffic events)
        if flag:
            base_pattern += random.uniform(0, 0.25)

        # Add small continuous random noise (normal fluctuations)
        noise = random.uniform(-self.noise_level, self.noise_level)
        base_pattern += noise

        # Scale down slightly and clamp result between 0 and 1 to avoid overshoot
        normalized = min(max(base_pattern / 1.4, 0), 1)

        # Advance time step for next reading (simulates real-time sensor behavior)
        self._time += 1

        # Return normalized CO₂ value (0 = very clean, 1 = maximum concentration)
        return normalized

    def generate_co2_data(self, flag=False):
        """
        Public method that converts the normalized CO₂ pattern (0–1)
        into a real-world CO₂ concentration in ppm.
        """
        # Get normalized pattern value for current time
        x = self._generate_normalized_value(flag)

        # Scale normalized 0–1 value into actual ppm range (min_ppm → max_ppm)
        y = (self.max_ppm - self.min_ppm) * x + self.min_ppm

        # Round to 2 decimal places for cleaner readings
        return round(y, 2)


# ---------------- Driver Code ----------------
if __name__ == "__main__":
    generator = CO2DataGenerator()
    readings_per_hour = generator.readings_per_hour
    total_hours = 24
    number_of_values = total_hours * readings_per_hour

    # Generate CO2 readings
    co2_values = [generator.generate_co2_data((x % 50) > 24) for x in range(number_of_values)]

    # Generate x-axis in hours (fractional hours)
    hours = [x / readings_per_hour for x in range(number_of_values)]

    # Plot
    plt.figure(figsize=(12, 5))
    plt.plot(hours, co2_values, 'g', marker='o', markersize=3)
    plt.title(f"Simulated Roadside CO₂ Emission Over {total_hours} Hours")
    plt.xlabel("Hour of Day")
    plt.ylabel("CO₂ Concentration (ppm)")
    plt.xticks(range(0, 25, 1))  # ticks at each hour
    plt.grid(True)
    plt.show()

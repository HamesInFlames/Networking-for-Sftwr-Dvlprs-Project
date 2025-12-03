import time
import random
import json
from lab_data_generator_co2 import CO2DataGenerator


#  STARTING ID FOR SEQUENCE
start_id = 111
_generator = CO2DataGenerator()   # your previous lab generator


#  CREATE A NESTED PAYLOAD (dict)
def create_data():
    global start_id
    start_id += 1  # increment sequence number

    co2_value = _generator.generate_co2_data()  # Lab 8

    payload = {
        "id": start_id,
        "timestamp": time.asctime(),
        "location": {"room": "Computer Lab 3","building": "Progress Campus"},
        "environment": {"co2_ppm": co2_value,"temperature_c": round(random.gauss(22, 1), 2),"humidity_percent": round(random.gauss(45, 3), 2)},
        "device": {"status": "active","battery_level": random.randint(65, 100),},
        "alerts": {"co2_high": co2_value > 1200,"temperature_warning": False}
    }
    return payload


#   PRINT DICTIONARY
def print_data(data: dict):
    print("\n---- RECEIVED MQTT DATA ----")
    print(json.dumps(data, indent=4))
    print("------------------------------\n")

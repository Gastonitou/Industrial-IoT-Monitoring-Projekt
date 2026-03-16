import random
import datetime
import json


MACHINE_IDS = ["MACHINE-01", "MACHINE-02", "MACHINE-03"]


def simulate_telemetry(machine_id: str | None = None) -> dict:
    if machine_id is None:
        machine_id = random.choice(MACHINE_IDS)

    temperature_c = round(random.uniform(40.0, 95.0), 2)
    vibration_mm_s = round(random.uniform(0.5, 10.0), 2)
    power_w = round(random.uniform(5000.0, 15000.0), 1)

    if temperature_c > 85 or vibration_mm_s > 7.5 or power_w > 12000:
        status = "ALERT"
    else:
        status = "RUNNING"

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "machine_id": machine_id,
        "temperature_c": temperature_c,
        "vibration_mm_s": vibration_mm_s,
        "power_w": power_w,
        "status": status,
    }


def payload_to_json(telemetry: dict) -> str:
    return json.dumps(telemetry)

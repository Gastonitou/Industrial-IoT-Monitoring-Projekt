import random
import datetime


def generate_telemetry(machine_id: str) -> dict:
    """Generate a simulated telemetry payload for a machine."""
    temperature_c = round(random.uniform(60.0, 95.0), 2)
    vibration_mm_s = round(random.uniform(1.0, 10.0), 2)
    power_w = round(random.uniform(6000.0, 14000.0), 2)

    if temperature_c > 85 or vibration_mm_s > 7.5 or power_w > 12000:
        status = "WARNING"
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

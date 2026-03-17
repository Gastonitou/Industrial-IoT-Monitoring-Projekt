import random
import datetime
import json
from src.common.config import (
    WARN_TEMP_MAX, WARN_VIBRATION_MAX, WARN_POWER_MAX,
    ALERT_TEMP_MAX, ALERT_VIBRATION_MAX, ALERT_POWER_MAX,
)


MACHINE_IDS = ["MACHINE-01", "MACHINE-02", "MACHINE-03"]


def simulate_telemetry(machine_id: str | None = None) -> dict:
    if machine_id is None:
        machine_id = random.choice(MACHINE_IDS)

    temperature_c = round(random.uniform(40.0, 95.0), 2)
    vibration_mm_s = round(random.uniform(0.5, 10.0), 2)
    power_w = round(random.uniform(5000.0, 15000.0), 1)

    if temperature_c > ALERT_TEMP_MAX or vibration_mm_s > ALERT_VIBRATION_MAX or power_w > ALERT_POWER_MAX:
        status = "ALERT"
        status_code = 2
    elif temperature_c > WARN_TEMP_MAX or vibration_mm_s > WARN_VIBRATION_MAX or power_w > WARN_POWER_MAX:
        status = "WARNING"
        status_code = 1
    else:
        status = "RUNNING"
        status_code = 0

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "machine_id": machine_id,
        "temperature_c": temperature_c,
        "vibration_mm_s": vibration_mm_s,
        "power_w": power_w,
        "status": status,
        "status_code": status_code,
    }


def payload_to_json(telemetry: dict) -> str:
    return json.dumps(telemetry)

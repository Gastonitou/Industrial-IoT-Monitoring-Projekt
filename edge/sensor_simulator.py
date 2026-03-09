"""
sensor_simulator.py
====================
Simulates industrial sensor readings for temperature, vibration, and
power consumption on multiple machines.

Can be imported as a module (for testing / subscriber integration) or
run directly as a standalone edge script that publishes via MQTT.
"""

from __future__ import annotations

import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ─── Data classes ────────────────────────────────────────────────────────────────

@dataclass
class SensorReading:
    """A single sensor measurement."""
    machine_id: str
    machine_name: str
    location: str
    sensor_type: str          # "temperature" | "vibration" | "power_consumption"
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    is_anomaly: bool = False

    def to_dict(self) -> dict:
        return {
            "machine_id": self.machine_id,
            "machine_name": self.machine_name,
            "location": self.location,
            "sensor_type": self.sensor_type,
            "value": round(self.value, 3),
            "unit": self.unit,
            "timestamp": self.timestamp,
            "is_anomaly": self.is_anomaly,
        }


@dataclass
class SensorConfig:
    """Operating limits for a single sensor type on a machine."""
    sensor_type: str
    normal_min: float
    normal_max: float
    alert_min: float
    alert_max: float


@dataclass
class MachineConfig:
    """Configuration for one physical machine."""
    machine_id: str
    name: str
    location: str
    sensors: List[SensorConfig]


# ─── Unit map ────────────────────────────────────────────────────────────────────

SENSOR_UNITS: Dict[str, str] = {
    "temperature": "°C",
    "vibration": "mm/s",
    "power_consumption": "kW",
}


# ─── Simulator ───────────────────────────────────────────────────────────────────

class SensorSimulator:
    """
    Generates realistic synthetic sensor readings for a list of machines.

    Normal readings follow a smooth sine-wave trend with added Gaussian
    noise.  Anomalies are generated with probability ``anomaly_probability``
    and land outside the sensor's *alert* thresholds.
    """

    def __init__(
        self,
        machines: List[MachineConfig],
        anomaly_probability: float = 0.05,
        seed: Optional[int] = None,
    ) -> None:
        self.machines = machines
        self.anomaly_probability = anomaly_probability
        self._rng = random.Random(seed)
        self._np_rng = np.random.default_rng(seed)
        # Per-machine phase offsets so trends are not identical
        self._phase: Dict[str, float] = {
            m.machine_id: self._rng.uniform(0, 2 * math.pi) for m in machines
        }
        self._tick = 0

    # ── Public API ───────────────────────────────────────────────────────────────

    def generate_readings(self) -> List[SensorReading]:
        """Return one reading per sensor per machine."""
        readings: List[SensorReading] = []
        for machine in self.machines:
            for sensor_cfg in machine.sensors:
                reading = self._generate_single(machine, sensor_cfg)
                readings.append(reading)
        self._tick += 1
        return readings

    # ── Internals ────────────────────────────────────────────────────────────────

    def _generate_single(
        self, machine: MachineConfig, sensor: SensorConfig
    ) -> SensorReading:
        is_anomaly = self._rng.random() < self.anomaly_probability

        if is_anomaly:
            # Generate a value outside the alert range (above or below)
            if self._rng.random() < 0.5:
                value = self._rng.uniform(sensor.alert_max * 1.05, sensor.alert_max * 1.30)
            else:
                low = sensor.alert_min - abs(sensor.alert_min * 0.30) - 0.1
                value = self._rng.uniform(low, sensor.alert_min * 0.95)
        else:
            # Sine-wave baseline + Gaussian noise within normal range
            phase = self._phase[machine.machine_id]
            mid = (sensor.normal_min + sensor.normal_max) / 2.0
            amplitude = (sensor.normal_max - sensor.normal_min) / 4.0
            trend = mid + amplitude * math.sin(self._tick * 0.1 + phase)
            noise = self._np_rng.normal(0, amplitude * 0.1)
            value = float(np.clip(trend + noise, sensor.normal_min, sensor.normal_max))

        unit = SENSOR_UNITS.get(sensor.sensor_type, "")
        return SensorReading(
            machine_id=machine.machine_id,
            machine_name=machine.name,
            location=machine.location,
            sensor_type=sensor.sensor_type,
            value=value,
            unit=unit,
            is_anomaly=is_anomaly,
        )


# ─── Factory helper ──────────────────────────────────────────────────────────────

def load_machines_from_config(config: dict) -> List[MachineConfig]:
    """Build :class:`MachineConfig` objects from a parsed YAML config dict."""
    machines: List[MachineConfig] = []
    for m in config.get("machines", []):
        sensors = [
            SensorConfig(
                sensor_type=s["type"],
                normal_min=s["normal_min"],
                normal_max=s["normal_max"],
                alert_min=s["alert_min"],
                alert_max=s["alert_max"],
            )
            for s in m.get("sensors", [])
        ]
        machines.append(
            MachineConfig(
                machine_id=m["id"],
                name=m["name"],
                location=m["location"],
                sensors=sensors,
            )
        )
    return machines


# ─── Standalone entry-point ──────────────────────────────────────────────────────

def _main() -> None:
    import json
    import os
    import sys

    import yaml

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config", "config.yaml"
    )
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    machines = load_machines_from_config(cfg)
    interval = cfg.get("simulation", {}).get("publish_interval_seconds", 5)
    anomaly_prob = cfg.get("simulation", {}).get("anomaly_probability", 0.05)

    simulator = SensorSimulator(machines, anomaly_probability=anomaly_prob)

    logger.info("Sensor simulator started (standalone mode). Press Ctrl+C to stop.")
    try:
        while True:
            readings = simulator.generate_readings()
            for r in readings:
                label = "⚠ ANOMALY" if r.is_anomaly else "OK"
                logger.info(
                    "[%s] %s | %s = %.3f %s  [%s]",
                    r.machine_id,
                    r.machine_name,
                    r.sensor_type,
                    r.value,
                    r.unit,
                    label,
                )
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Simulator stopped.")
        sys.exit(0)


if __name__ == "__main__":
    _main()

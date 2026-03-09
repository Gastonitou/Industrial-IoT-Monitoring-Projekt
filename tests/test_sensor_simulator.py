"""
tests/test_sensor_simulator.py
================================
Unit tests for the SensorSimulator module.
"""

import sys
import time
from pathlib import Path

import pytest

# Make sure the edge package is importable without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "edge"))

from sensor_simulator import (
    MachineConfig,
    SensorConfig,
    SensorReading,
    SensorSimulator,
    load_machines_from_config,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture()
def sample_sensor():
    return SensorConfig(
        sensor_type="temperature",
        normal_min=20.0,
        normal_max=80.0,
        alert_min=10.0,
        alert_max=95.0,
    )


@pytest.fixture()
def sample_machine(sample_sensor):
    return MachineConfig(
        machine_id="test_machine",
        name="Test Machine",
        location="Hall X",
        sensors=[sample_sensor],
    )


@pytest.fixture()
def simulator(sample_machine):
    return SensorSimulator(
        machines=[sample_machine],
        anomaly_probability=0.0,  # deterministic: no anomalies
        seed=42,
    )


@pytest.fixture()
def anomaly_simulator(sample_machine):
    return SensorSimulator(
        machines=[sample_machine],
        anomaly_probability=1.0,  # always produce anomalies
        seed=0,
    )


# ─── SensorReading ────────────────────────────────────────────────────────────────


class TestSensorReading:
    def test_to_dict_contains_required_keys(self, sample_machine, sample_sensor):
        reading = SensorReading(
            machine_id="m1",
            machine_name="M1",
            location="Hall A",
            sensor_type="temperature",
            value=55.5,
            unit="°C",
        )
        d = reading.to_dict()
        for key in ("machine_id", "machine_name", "location", "sensor_type", "value", "unit", "timestamp", "is_anomaly"):
            assert key in d

    def test_value_is_rounded_to_3dp(self):
        reading = SensorReading(
            machine_id="m1", machine_name="M1", location="L",
            sensor_type="temperature", value=55.12345678, unit="°C",
        )
        assert reading.to_dict()["value"] == round(55.12345678, 3)

    def test_default_timestamp_is_recent(self):
        before = time.time()
        reading = SensorReading(
            machine_id="m1", machine_name="M1", location="L",
            sensor_type="temperature", value=50.0, unit="°C",
        )
        after = time.time()
        assert before <= reading.timestamp <= after


# ─── SensorSimulator ─────────────────────────────────────────────────────────────


class TestSensorSimulator:
    def test_generate_readings_count(self, simulator, sample_machine):
        readings = simulator.generate_readings()
        # 1 machine × 1 sensor = 1 reading
        assert len(readings) == len(sample_machine.sensors)

    def test_normal_readings_within_bounds(self, simulator, sample_sensor):
        for _ in range(50):
            readings = simulator.generate_readings()
            for r in readings:
                assert sample_sensor.normal_min <= r.value <= sample_sensor.normal_max

    def test_anomaly_readings_outside_alert_range(self, anomaly_simulator, sample_sensor):
        found_anomaly = False
        for _ in range(20):
            readings = anomaly_simulator.generate_readings()
            for r in readings:
                if r.is_anomaly:
                    found_anomaly = True
                    # Anomaly should be outside the *normal* range
                    assert (
                        r.value < sample_sensor.normal_min
                        or r.value > sample_sensor.normal_max
                    )
        assert found_anomaly, "Expected at least one anomaly reading"

    def test_reading_has_correct_unit(self, simulator):
        readings = simulator.generate_readings()
        for r in readings:
            assert r.unit == "°C"

    def test_machine_metadata_on_reading(self, simulator, sample_machine):
        readings = simulator.generate_readings()
        r = readings[0]
        assert r.machine_id == sample_machine.machine_id
        assert r.machine_name == sample_machine.name
        assert r.location == sample_machine.location

    def test_multiple_machines(self):
        machines = [
            MachineConfig(
                machine_id=f"m{i}",
                name=f"Machine {i}",
                location="Hall",
                sensors=[
                    SensorConfig("temperature", 20, 80, 10, 95),
                    SensorConfig("vibration", 0, 5, 0, 8),
                ],
            )
            for i in range(3)
        ]
        sim = SensorSimulator(machines, anomaly_probability=0.0, seed=1)
        readings = sim.generate_readings()
        # 3 machines × 2 sensors = 6 readings
        assert len(readings) == 6

    def test_tick_increments(self, simulator):
        assert simulator._tick == 0
        simulator.generate_readings()
        assert simulator._tick == 1
        simulator.generate_readings()
        assert simulator._tick == 2


# ─── load_machines_from_config ───────────────────────────────────────────────────


class TestLoadMachinesFromConfig:
    def test_loads_machines(self):
        cfg = {
            "machines": [
                {
                    "id": "m1",
                    "name": "Machine 1",
                    "location": "Hall A",
                    "sensors": [
                        {
                            "type": "temperature",
                            "normal_min": 20.0,
                            "normal_max": 80.0,
                            "alert_min": 10.0,
                            "alert_max": 95.0,
                        }
                    ],
                }
            ]
        }
        machines = load_machines_from_config(cfg)
        assert len(machines) == 1
        assert machines[0].machine_id == "m1"
        assert len(machines[0].sensors) == 1
        assert machines[0].sensors[0].sensor_type == "temperature"

    def test_empty_config(self):
        assert load_machines_from_config({}) == []

    def test_machine_without_sensors(self):
        cfg = {
            "machines": [
                {"id": "m1", "name": "M1", "location": "L", "sensors": []}
            ]
        }
        machines = load_machines_from_config(cfg)
        assert machines[0].sensors == []

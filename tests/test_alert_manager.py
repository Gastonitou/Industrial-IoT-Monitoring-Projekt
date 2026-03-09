"""
tests/test_alert_manager.py
============================
Unit tests for the AlertManager module.
"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from alert_manager import (
    Alert,
    AlertLevel,
    AlertManager,
    AlertThreshold,
    build_alert_manager_from_config,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture()
def threshold():
    return AlertThreshold(
        sensor_type="temperature",
        warning_min=15.0,
        warning_max=85.0,
        critical_min=10.0,
        critical_max=95.0,
    )


@pytest.fixture()
def manager(threshold):
    return AlertManager(
        thresholds={"machine_01": [threshold]},
        email_enabled=False,
    )


def _make_reading(
    value: float,
    machine_id: str = "machine_01",
    sensor_type: str = "temperature",
    unit: str = "°C",
) -> dict:
    return {
        "machine_id": machine_id,
        "machine_name": "CNC Lathe #1",
        "location": "Hall A",
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit,
        "timestamp": time.time(),
        "is_anomaly": False,
    }


# ─── AlertThreshold classification ──────────────────────────────────────────────


class TestClassification:
    def test_ok_within_warning_range(self, threshold):
        assert AlertManager._classify(50.0, threshold) == AlertLevel.OK

    def test_warning_below_warning_min(self, threshold):
        # Between critical_min (10) and warning_min (15)
        assert AlertManager._classify(12.0, threshold) == AlertLevel.WARNING

    def test_warning_above_warning_max(self, threshold):
        # Between warning_max (85) and critical_max (95)
        assert AlertManager._classify(90.0, threshold) == AlertLevel.WARNING

    def test_critical_below_critical_min(self, threshold):
        assert AlertManager._classify(5.0, threshold) == AlertLevel.CRITICAL

    def test_critical_above_critical_max(self, threshold):
        assert AlertManager._classify(100.0, threshold) == AlertLevel.CRITICAL

    def test_boundary_at_warning_min(self, threshold):
        # Exactly at warning_min → OK
        assert AlertManager._classify(15.0, threshold) == AlertLevel.OK

    def test_boundary_at_critical_max(self, threshold):
        # Exactly at critical_max (95.0) is above warning_max (85.0) but not above
        # critical_max, so it should be WARNING, not CRITICAL.
        assert AlertManager._classify(95.0, threshold) == AlertLevel.WARNING


# ─── AlertManager.evaluate ───────────────────────────────────────────────────────


class TestAlertManagerEvaluate:
    def test_ok_reading_returns_none(self, manager):
        assert manager.evaluate(_make_reading(50.0)) is None

    def test_warning_returns_alert(self, manager):
        alert = manager.evaluate(_make_reading(12.0))
        assert alert is not None
        assert alert.level == AlertLevel.WARNING

    def test_critical_returns_alert(self, manager):
        alert = manager.evaluate(_make_reading(5.0))
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL

    def test_unknown_machine_returns_none(self, manager):
        assert manager.evaluate(_make_reading(5.0, machine_id="unknown_machine")) is None

    def test_unknown_sensor_type_returns_none(self, manager):
        reading = _make_reading(999.0)
        reading["sensor_type"] = "pressure"
        assert manager.evaluate(reading) is None

    def test_alert_contains_correct_metadata(self, manager):
        alert = manager.evaluate(_make_reading(5.0))
        assert alert.machine_id == "machine_01"
        assert alert.sensor_type == "temperature"
        assert alert.value == 5.0

    def test_alert_to_dict(self, manager):
        alert = manager.evaluate(_make_reading(5.0))
        d = alert.to_dict()
        for key in ("machine_id", "machine_name", "sensor_type", "value", "unit", "level", "message", "timestamp"):
            assert key in d


# ─── build_alert_manager_from_config ─────────────────────────────────────────────


class TestBuildAlertManagerFromConfig:
    def _config(self):
        return {
            "machines": [
                {
                    "id": "m1",
                    "name": "M1",
                    "location": "L",
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

    def test_creates_manager(self):
        mgr = build_alert_manager_from_config(self._config())
        assert isinstance(mgr, AlertManager)

    def test_thresholds_loaded(self):
        mgr = build_alert_manager_from_config(self._config())
        # Critical value should trigger an alert
        alert = mgr.evaluate(
            {
                "machine_id": "m1",
                "machine_name": "M1",
                "location": "L",
                "sensor_type": "temperature",
                "value": 5.0,  # below alert_min=10
                "unit": "°C",
                "timestamp": time.time(),
            }
        )
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL

    def test_empty_config(self):
        mgr = build_alert_manager_from_config({})
        assert mgr.evaluate(_make_reading(999.0, machine_id="any")) is None

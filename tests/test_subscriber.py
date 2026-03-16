import unittest
from src.backend.subscriber import check_alerts


class TestAlertDetection(unittest.TestCase):
    def _make_telemetry(self, temp=60.0, vib=3.0, power=8000.0):
        return {
            "timestamp": "2026-03-09T10:15:35.123456+00:00",
            "machine_id": "MACHINE-01",
            "temperature_c": temp,
            "vibration_mm_s": vib,
            "power_w": power,
            "status": "RUNNING",
        }

    def test_no_alert(self):
        telemetry = self._make_telemetry()
        alerts = check_alerts(telemetry)
        self.assertEqual(alerts, [])

    def test_high_temperature_alert(self):
        telemetry = self._make_telemetry(temp=90.0)
        alerts = check_alerts(telemetry)
        self.assertTrue(any("HIGH_TEMPERATURE" in a for a in alerts))

    def test_high_vibration_alert(self):
        telemetry = self._make_telemetry(vib=9.0)
        alerts = check_alerts(telemetry)
        self.assertTrue(any("HIGH_VIBRATION" in a for a in alerts))

    def test_high_power_alert(self):
        telemetry = self._make_telemetry(power=13000.0)
        alerts = check_alerts(telemetry)
        self.assertTrue(any("HIGH_POWER" in a for a in alerts))

    def test_multiple_alerts(self):
        telemetry = self._make_telemetry(temp=90.0, vib=9.0, power=13000.0)
        alerts = check_alerts(telemetry)
        self.assertEqual(len(alerts), 3)


if __name__ == "__main__":
    unittest.main()

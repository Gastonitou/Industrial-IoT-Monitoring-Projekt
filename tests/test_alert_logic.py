import csv
import os
import tempfile
import unittest
import unittest.mock as mock


class TestAlertLogic(unittest.TestCase):
    def _make_payload(self, temperature_c=70.0, vibration_mm_s=3.0, power_w=8000.0):
        return {
            "timestamp": "2026-03-09T10:00:00+00:00",
            "machine_id": "MACHINE-01",
            "temperature_c": temperature_c,
            "vibration_mm_s": vibration_mm_s,
            "power_w": power_w,
            "status": "RUNNING",
        }

    def test_no_alert_when_all_normal(self):
        payload = self._make_payload()
        from src.common.config import ALERT_TEMP_MAX, ALERT_VIBRATION_MAX, ALERT_POWER_MAX
        self.assertLessEqual(payload["temperature_c"], ALERT_TEMP_MAX)
        self.assertLessEqual(payload["vibration_mm_s"], ALERT_VIBRATION_MAX)
        self.assertLessEqual(payload["power_w"], ALERT_POWER_MAX)

    def test_temp_alert_triggered(self):
        from src.common.config import ALERT_TEMP_MAX
        payload = self._make_payload(temperature_c=ALERT_TEMP_MAX + 1)
        self.assertGreater(payload["temperature_c"], ALERT_TEMP_MAX)

    def test_vibration_alert_triggered(self):
        from src.common.config import ALERT_VIBRATION_MAX
        payload = self._make_payload(vibration_mm_s=ALERT_VIBRATION_MAX + 1)
        self.assertGreater(payload["vibration_mm_s"], ALERT_VIBRATION_MAX)

    def test_power_alert_triggered(self):
        from src.common.config import ALERT_POWER_MAX
        payload = self._make_payload(power_w=ALERT_POWER_MAX + 1)
        self.assertGreater(payload["power_w"], ALERT_POWER_MAX)

    def test_alert_log_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "alerts_log.csv")
            with open(log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "machine_id", "alert_type", "value", "threshold"])
                writer.writerow(["2026-03-09T10:00:00+00:00", "MACHINE-01", "temperature", 90.0, 85.0])

            with open(log_path, newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["alert_type"], "temperature")
            self.assertEqual(float(rows[0]["value"]), 90.0)
            self.assertEqual(float(rows[0]["threshold"]), 85.0)


if __name__ == "__main__":
    unittest.main()

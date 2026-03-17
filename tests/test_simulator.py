import unittest
from src.simulator.sensor_simulator import simulate_telemetry, payload_to_json
import json


class TestSensorSimulator(unittest.TestCase):
    def test_telemetry_keys(self):
        data = simulate_telemetry("MACHINE-01")
        for key in ["timestamp", "machine_id", "temperature_c", "vibration_mm_s", "power_w", "status", "status_code"]:
            self.assertIn(key, data)

    def test_machine_id(self):
        data = simulate_telemetry("MACHINE-99")
        self.assertEqual(data["machine_id"], "MACHINE-99")

    def test_status_alert(self):
        import unittest.mock as mock
        with mock.patch("src.simulator.sensor_simulator.random.uniform", side_effect=[90.0, 3.0, 8000.0]):
            data = simulate_telemetry("MACHINE-01")
            self.assertEqual(data["status"], "ALERT")
            self.assertEqual(data["status_code"], 2)

    def test_status_warning(self):
        import unittest.mock as mock
        # temperature in warning range (75 < 80 < 85), vibration and power safe
        with mock.patch("src.simulator.sensor_simulator.random.uniform", side_effect=[80.0, 3.0, 8000.0]):
            data = simulate_telemetry("MACHINE-01")
            self.assertEqual(data["status"], "WARNING")
            self.assertEqual(data["status_code"], 1)

    def test_status_running(self):
        import unittest.mock as mock
        with mock.patch("src.simulator.sensor_simulator.random.uniform", side_effect=[60.0, 3.0, 8000.0]):
            data = simulate_telemetry("MACHINE-01")
            self.assertEqual(data["status"], "RUNNING")
            self.assertEqual(data["status_code"], 0)

    def test_payload_to_json(self):
        data = simulate_telemetry("MACHINE-01")
        payload = payload_to_json(data)
        parsed = json.loads(payload)
        self.assertEqual(parsed["machine_id"], "MACHINE-01")


if __name__ == "__main__":
    unittest.main()

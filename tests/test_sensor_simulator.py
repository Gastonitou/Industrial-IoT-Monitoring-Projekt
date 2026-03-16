import unittest
from src.simulator.sensor_simulator import generate_telemetry


class TestSensorSimulator(unittest.TestCase):
    def test_telemetry_keys(self):
        payload = generate_telemetry("MACHINE-01")
        expected_keys = {"timestamp", "machine_id", "temperature_c", "vibration_mm_s", "power_w", "status"}
        self.assertEqual(set(payload.keys()), expected_keys)

    def test_machine_id(self):
        payload = generate_telemetry("MACHINE-42")
        self.assertEqual(payload["machine_id"], "MACHINE-42")

    def test_temperature_range(self):
        for _ in range(50):
            payload = generate_telemetry("MACHINE-01")
            self.assertGreaterEqual(payload["temperature_c"], 60.0)
            self.assertLessEqual(payload["temperature_c"], 95.0)

    def test_vibration_range(self):
        for _ in range(50):
            payload = generate_telemetry("MACHINE-01")
            self.assertGreaterEqual(payload["vibration_mm_s"], 1.0)
            self.assertLessEqual(payload["vibration_mm_s"], 10.0)

    def test_power_range(self):
        for _ in range(50):
            payload = generate_telemetry("MACHINE-01")
            self.assertGreaterEqual(payload["power_w"], 6000.0)
            self.assertLessEqual(payload["power_w"], 14000.0)

    def test_status_warning_when_temp_high(self):
        import unittest.mock as mock
        import random
        with mock.patch.object(random, "uniform", side_effect=[90.0, 3.0, 8000.0]):
            payload = generate_telemetry("MACHINE-01")
            self.assertEqual(payload["status"], "WARNING")

    def test_status_running_when_all_normal(self):
        import unittest.mock as mock
        import random
        with mock.patch.object(random, "uniform", side_effect=[70.0, 3.0, 8000.0]):
            payload = generate_telemetry("MACHINE-01")
            self.assertEqual(payload["status"], "RUNNING")


if __name__ == "__main__":
    unittest.main()

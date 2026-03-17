import os
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC_TEMPLATE = "factory/machines/{machine_id}/telemetry"

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "iot-org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "iot_metrics")

WARN_TEMP_MAX = float(os.getenv("WARN_TEMP_MAX", 75))
WARN_VIBRATION_MAX = float(os.getenv("WARN_VIBRATION_MAX", 6.0))
WARN_POWER_MAX = float(os.getenv("WARN_POWER_MAX", 10500))

ALERT_TEMP_MAX = float(os.getenv("ALERT_TEMP_MAX", 85))
ALERT_VIBRATION_MAX = float(os.getenv("ALERT_VIBRATION_MAX", 7.5))
ALERT_POWER_MAX = float(os.getenv("ALERT_POWER_MAX", 12000))

ALERTS_LOG_PATH = os.getenv("ALERTS_LOG_PATH", "data/alerts_log.csv")

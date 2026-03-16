import os
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "factory/machines/MACHINE-01/telemetry")

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "industrial-iot-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "industrial-iot")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "industrial-iot")

ALERT_TEMP_MAX = float(os.getenv("ALERT_TEMP_MAX", "85"))
ALERT_VIBRATION_MAX = float(os.getenv("ALERT_VIBRATION_MAX", "7.5"))
ALERT_POWER_MAX = float(os.getenv("ALERT_POWER_MAX", "12000"))

MACHINE_ID = os.getenv("MACHINE_ID", "MACHINE-01")
PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "5"))

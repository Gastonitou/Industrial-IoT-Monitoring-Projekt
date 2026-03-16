import csv
import json
import logging
import os
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from src.common.config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_TOPIC,
    INFLUXDB_URL,
    INFLUXDB_TOKEN,
    INFLUXDB_ORG,
    INFLUXDB_BUCKET,
    ALERT_TEMP_MAX,
    ALERT_VIBRATION_MAX,
    ALERT_POWER_MAX,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ALERTS_LOG_PATH = os.path.join("data", "alerts_log.csv")
ALERTS_LOG_HEADER = ["timestamp", "machine_id", "alert_type", "value", "threshold"]


def _ensure_alerts_log():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(ALERTS_LOG_PATH):
        with open(ALERTS_LOG_PATH, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(ALERTS_LOG_HEADER)


def _log_alert(timestamp: str, machine_id: str, alert_type: str, value: float, threshold: float):
    with open(ALERTS_LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, machine_id, alert_type, value, threshold])
    logger.warning("ALERT [%s] machine=%s value=%s threshold=%s", alert_type, machine_id, value, threshold)


def _check_alerts(payload: dict):
    ts = payload["timestamp"]
    mid = payload["machine_id"]
    if payload["temperature_c"] > ALERT_TEMP_MAX:
        _log_alert(ts, mid, "temperature", payload["temperature_c"], ALERT_TEMP_MAX)
    if payload["vibration_mm_s"] > ALERT_VIBRATION_MAX:
        _log_alert(ts, mid, "vibration", payload["vibration_mm_s"], ALERT_VIBRATION_MAX)
    if payload["power_w"] > ALERT_POWER_MAX:
        _log_alert(ts, mid, "power", payload["power_w"], ALERT_POWER_MAX)


def run():
    _ensure_alerts_log()

    influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    def on_connect(client, userdata, flags, rc):
        logger.info("Connected to MQTT broker (rc=%s). Subscribing to %s", rc, MQTT_TOPIC)
        client.subscribe(MQTT_TOPIC)

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logger.info("Received: %s", payload)

            point = (
                Point("machine_telemetry")
                .tag("machine_id", payload["machine_id"])
                .tag("status", payload["status"])
                .field("temperature_c", float(payload["temperature_c"]))
                .field("vibration_mm_s", float(payload["vibration_mm_s"]))
                .field("power_w", float(payload["power_w"]))
                .time(payload["timestamp"], WritePrecision.NS)
            )
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

            _check_alerts(payload)
        except Exception as e:
            logger.error("Error processing message: %s", e)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    logger.info("Subscriber started.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Subscriber stopped.")
    finally:
        influx_client.close()


if __name__ == "__main__":
    run()

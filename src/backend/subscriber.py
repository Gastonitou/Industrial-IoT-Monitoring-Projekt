import json
import csv
import os
import datetime
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from src.common.config import (
    MQTT_BROKER,
    MQTT_PORT,
    INFLUXDB_URL,
    INFLUXDB_TOKEN,
    INFLUXDB_ORG,
    INFLUXDB_BUCKET,
    ALERT_TEMP_MAX,
    ALERT_VIBRATION_MAX,
    ALERT_POWER_MAX,
    ALERTS_LOG_PATH,
)


def check_alerts(telemetry: dict) -> list[str]:
    alerts = []
    if telemetry["temperature_c"] > ALERT_TEMP_MAX:
        alerts.append(f"HIGH_TEMPERATURE:{telemetry['temperature_c']}C")
    if telemetry["vibration_mm_s"] > ALERT_VIBRATION_MAX:
        alerts.append(f"HIGH_VIBRATION:{telemetry['vibration_mm_s']}mm/s")
    if telemetry["power_w"] > ALERT_POWER_MAX:
        alerts.append(f"HIGH_POWER:{telemetry['power_w']}W")
    return alerts


def log_alert(telemetry: dict, alerts: list[str]):
    os.makedirs(os.path.dirname(ALERTS_LOG_PATH), exist_ok=True)
    file_exists = os.path.isfile(ALERTS_LOG_PATH)
    with open(ALERTS_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["timestamp", "machine_id", "alert_type", "value"]
        )
        if not file_exists:
            writer.writeheader()
        for alert in alerts:
            alert_type, value = alert.split(":", 1)
            writer.writerow(
                {
                    "timestamp": telemetry["timestamp"],
                    "machine_id": telemetry["machine_id"],
                    "alert_type": alert_type,
                    "value": value,
                }
            )


def write_to_influxdb(write_api, telemetry: dict):
    point = (
        Point("machine_telemetry")
        .tag("machine_id", telemetry["machine_id"])
        .tag("status", telemetry["status"])
        .field("temperature_c", telemetry["temperature_c"])
        .field("vibration_mm_s", telemetry["vibration_mm_s"])
        .field("power_w", telemetry["power_w"])
        .field("status_code", int(telemetry.get("status_code", 0)))
        .time(telemetry["timestamp"], WritePrecision.NANOSECONDS)
    )
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)


def run_subscriber():
    influx_client = InfluxDBClient(
        url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
    )
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    def on_message(client, userdata, msg):
        try:
            telemetry = json.loads(msg.payload.decode())
            print(f"Received: {telemetry}")
            write_to_influxdb(write_api, telemetry)
            alerts = check_alerts(telemetry)
            if alerts:
                print(f"ALERTS: {alerts}")
                log_alert(telemetry, alerts)
        except Exception as e:
            print(f"Error processing message: {e}")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("factory/machines/+/telemetry")
            print("Subscribed to factory/machines/+/telemetry")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    print("Subscriber running. Waiting for messages...")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Subscriber stopped.")
    finally:
        influx_client.close()


if __name__ == "__main__":
    run_subscriber()

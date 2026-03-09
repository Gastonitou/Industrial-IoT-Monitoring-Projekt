"""
mqtt_subscriber.py
===================
Backend service that:

1. Subscribes to all machine sensor topics on the MQTT broker.
2. Parses incoming JSON payloads.
3. Writes each reading to InfluxDB.
4. Passes every reading through the :class:`AlertManager`.

Topics subscribed::

    factory/machines/+/+   (wildcard: any machine, any sensor)
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

import paho.mqtt.client as mqtt
import yaml
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# ── Local import ─────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from alert_manager import build_alert_manager_from_config

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Config helpers ──────────────────────────────────────────────────────────────

def _load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _setup_logging(cfg: dict) -> None:
    log_cfg = cfg.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    log_file = log_cfg.get("file", "logs/iot_monitoring.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    from logging.handlers import RotatingFileHandler

    handler = RotatingFileHandler(
        log_file,
        maxBytes=log_cfg.get("max_bytes", 10_485_760),
        backupCount=log_cfg.get("backup_count", 5),
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logging.getLogger().setLevel(level)
    logging.getLogger().addHandler(handler)


# ─── InfluxDB writer ─────────────────────────────────────────────────────────────

class InfluxDBWriter:
    """Thin wrapper around the InfluxDB v2 write client."""

    def __init__(self, cfg: dict) -> None:
        influx_cfg = cfg.get("influxdb", {})
        url = os.getenv("INFLUXDB_URL") or influx_cfg.get("url", "http://localhost:8086")
        token = os.getenv("INFLUXDB_TOKEN") or influx_cfg.get("token", "")
        self._org = os.getenv("INFLUXDB_ORG") or influx_cfg.get("org", "iot-org")
        self._bucket = os.getenv("INFLUXDB_BUCKET") or influx_cfg.get(
            "bucket", "iot-monitoring"
        )
        self._client = InfluxDBClient(url=url, token=token, org=self._org)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        logger.info("InfluxDB writer initialised (bucket=%s).", self._bucket)

    def write(self, reading: dict) -> None:
        """Write a single sensor reading dict to InfluxDB."""
        point = (
            Point("sensor_data")
            .tag("machine_id", reading["machine_id"])
            .tag("machine_name", reading["machine_name"])
            .tag("location", reading["location"])
            .tag("sensor_type", reading["sensor_type"])
            .tag("is_anomaly", str(reading.get("is_anomaly", False)))
            .field("value", float(reading["value"]))
            .field("unit", reading["unit"])
            .time(
                int(reading["timestamp"] * 1_000_000_000),
                WritePrecision.NANOSECONDS,
            )
        )
        self._write_api.write(bucket=self._bucket, org=self._org, record=point)
        logger.debug(
            "Written to InfluxDB: %s/%s = %.3f %s",
            reading["machine_id"],
            reading["sensor_type"],
            reading["value"],
            reading["unit"],
        )

    def close(self) -> None:
        self._client.close()


# ─── MQTT Subscriber ─────────────────────────────────────────────────────────────

class MQTTSubscriber:
    """Connects to the broker, subscribes to sensor topics, and processes messages."""

    def __init__(self, cfg: dict) -> None:
        self._cfg = cfg
        self._mqtt_cfg = cfg.get("mqtt", {})
        self._influx = InfluxDBWriter(cfg)
        self._alert_mgr = build_alert_manager_from_config(cfg)
        self._client = self._build_client()
        self._running = False

    # ── Lifecycle ────────────────────────────────────────────────────────────────

    def start(self) -> None:
        broker_host = os.getenv("MQTT_BROKER_HOST") or self._mqtt_cfg.get(
            "broker_host", "localhost"
        )
        broker_port = int(
            os.getenv("MQTT_BROKER_PORT") or self._mqtt_cfg.get("broker_port", 1883)
        )
        keepalive = self._mqtt_cfg.get("keepalive", 60)

        logger.info(
            "Connecting to MQTT broker at %s:%d …", broker_host, broker_port
        )
        self._client.connect(broker_host, broker_port, keepalive)
        self._running = True
        logger.info("Subscriber running. Waiting for messages …")
        self._client.loop_forever()

    def stop(self) -> None:
        self._running = False
        self._client.disconnect()
        self._influx.close()
        logger.info("Subscriber stopped.")

    # ── MQTT callbacks ───────────────────────────────────────────────────────────

    def _build_client(self) -> mqtt.Client:
        client_id = f"iot_subscriber_{os.getpid()}"
        client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        username = os.getenv("MQTT_USERNAME") or self._mqtt_cfg.get("username", "")
        password = os.getenv("MQTT_PASSWORD") or self._mqtt_cfg.get("password", "")
        if username:
            client.username_pw_set(username, password or None)

        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        return client

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc: int) -> None:
        if rc == 0:
            topic_prefix = self._mqtt_cfg.get("topic_prefix", "factory/machines")
            topic = f"{topic_prefix}/+/+"
            qos = self._mqtt_cfg.get("qos", 1)
            client.subscribe(topic, qos=qos)
            logger.info("Subscribed to '%s' (qos=%d).", topic, qos)
        else:
            logger.error("Failed to connect (rc=%d).", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata, rc: int) -> None:
        if rc != 0:
            logger.warning("Disconnected unexpectedly (rc=%d). Reconnecting…", rc)

    def _on_message(self, client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
        try:
            reading = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error("Invalid payload on topic %s: %s", msg.topic, exc)
            return

        logger.info(
            "Received ← %s | %s = %.3f %s",
            msg.topic,
            reading.get("sensor_type", "?"),
            reading.get("value", 0),
            reading.get("unit", ""),
        )

        # Write to InfluxDB
        try:
            self._influx.write(reading)
        except Exception as exc:
            logger.error("InfluxDB write error: %s", exc)

        # Evaluate alerts
        try:
            self._alert_mgr.evaluate(reading)
        except Exception as exc:
            logger.error("Alert evaluation error: %s", exc)


# ─── Entry-point ─────────────────────────────────────────────────────────────────

def main() -> None:
    cfg = _load_config()
    _setup_logging(cfg)

    subscriber = MQTTSubscriber(cfg)

    def _handle_signal(signum: int, frame: Optional[object]) -> None:
        logger.info("Signal %d received – shutting down.", signum)
        subscriber.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    subscriber.start()


if __name__ == "__main__":
    main()

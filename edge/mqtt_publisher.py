"""
mqtt_publisher.py
==================
Edge-device script that runs on the Raspberry Pi (or any Linux host).

Reads sensor data from :mod:`sensor_simulator`, serialises each reading
as JSON, and publishes it to the MQTT broker.

Topic structure::

    factory/machines/<machine_id>/<sensor_type>

Example::

    factory/machines/machine_01/temperature
    factory/machines/machine_01/vibration
    factory/machines/machine_01/power_consumption
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

# Local import
sys.path.insert(0, str(Path(__file__).parent))
from sensor_simulator import SensorSimulator, load_machines_from_config

# ─── Bootstrap ───────────────────────────────────────────────────────────────────

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


# ─── MQTT helpers ────────────────────────────────────────────────────────────────


def _build_client(cfg: dict) -> mqtt.Client:
    mqtt_cfg = cfg.get("mqtt", {})
    client_id = f"iot_publisher_{os.getpid()}"
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

    username = os.getenv("MQTT_USERNAME") or mqtt_cfg.get("username", "")
    password = os.getenv("MQTT_PASSWORD") or mqtt_cfg.get("password", "")
    if username:
        client.username_pw_set(username, password or None)

    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    client.on_publish = _on_publish
    return client


def _on_connect(client: mqtt.Client, userdata, flags, rc: int) -> None:
    if rc == 0:
        logger.info("Connected to MQTT broker.")
    else:
        logger.error("Failed to connect to MQTT broker (rc=%d).", rc)


def _on_disconnect(client: mqtt.Client, userdata, rc: int) -> None:
    if rc != 0:
        logger.warning("Unexpected disconnect from MQTT broker (rc=%d). Reconnecting…", rc)


def _on_publish(client: mqtt.Client, userdata, mid: int) -> None:
    logger.debug("Message published (mid=%d).", mid)


# ─── Publisher ───────────────────────────────────────────────────────────────────


class MQTTPublisher:
    """Connects to a broker and publishes sensor readings continuously."""

    def __init__(self, cfg: dict) -> None:
        self._cfg = cfg
        self._mqtt_cfg = cfg.get("mqtt", {})
        self._client = _build_client(cfg)
        self._simulator = SensorSimulator(
            machines=load_machines_from_config(cfg),
            anomaly_probability=cfg.get("simulation", {}).get("anomaly_probability", 0.05),
        )
        self._interval: float = cfg.get("simulation", {}).get(
            "publish_interval_seconds", 5
        )
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

        logger.info("Connecting to MQTT broker at %s:%d …", broker_host, broker_port)
        self._client.connect(broker_host, broker_port, keepalive)
        self._client.loop_start()

        self._running = True
        logger.info(
            "Publisher started. Publishing every %g seconds.", self._interval
        )
        try:
            while self._running:
                self._publish_cycle()
                time.sleep(self._interval)
        except KeyboardInterrupt:
            logger.info("Publisher interrupted by user.")
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("Publisher stopped.")

    # ── Internal ─────────────────────────────────────────────────────────────────

    def _publish_cycle(self) -> None:
        readings = self._simulator.generate_readings()
        topic_prefix = self._mqtt_cfg.get("topic_prefix", "factory/machines")
        qos = self._mqtt_cfg.get("qos", 1)

        for reading in readings:
            topic = f"{topic_prefix}/{reading.machine_id}/{reading.sensor_type}"
            payload = json.dumps(reading.to_dict())
            result = self._client.publish(topic, payload, qos=qos)

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.warning(
                    "Publish failed for %s (rc=%d).", topic, result.rc
                )
            else:
                level = logging.WARNING if reading.is_anomaly else logging.DEBUG
                logger.log(
                    level,
                    "Published → %s | value=%.3f %s%s",
                    topic,
                    reading.value,
                    reading.unit,
                    "  ⚠ ANOMALY" if reading.is_anomaly else "",
                )


# ─── Entry-point ─────────────────────────────────────────────────────────────────


def main() -> None:
    cfg = _load_config()
    _setup_logging(cfg)

    publisher = MQTTPublisher(cfg)

    def _handle_signal(signum: int, frame: Optional[object]) -> None:
        logger.info("Signal %d received – shutting down.", signum)
        publisher.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    publisher.start()


if __name__ == "__main__":
    main()

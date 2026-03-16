import json
import time
import logging
import paho.mqtt.client as mqtt
from src.common.config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_TOPIC,
    MACHINE_ID,
    PUBLISH_INTERVAL,
)
from src.simulator.sensor_simulator import generate_telemetry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    logger.info("Publisher started. Sending to %s every %ss", MQTT_TOPIC, PUBLISH_INTERVAL)
    try:
        while True:
            payload = generate_telemetry(MACHINE_ID)
            client.publish(MQTT_TOPIC, json.dumps(payload))
            logger.info("Published: %s", payload)
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Publisher stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()

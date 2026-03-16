import time
import json
import paho.mqtt.client as mqtt
from src.common.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_TEMPLATE
from src.simulator.sensor_simulator import simulate_telemetry, payload_to_json


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"Connection failed with code {rc}")


def run_publisher(machine_id: str = "MACHINE-01", interval: float = 5.0):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    topic = MQTT_TOPIC_TEMPLATE.format(machine_id=machine_id)
    print(f"Publishing telemetry on topic: {topic}")

    try:
        while True:
            telemetry = simulate_telemetry(machine_id)
            payload = payload_to_json(telemetry)
            client.publish(topic, payload)
            print(f"Published: {payload}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Publisher stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run_publisher()

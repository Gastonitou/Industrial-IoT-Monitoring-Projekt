# Architecture

## Overview

The system consists of the following components:

```
[Sensor Simulator] --> [Edge Publisher] --> [MQTT Broker] --> [Backend Subscriber]
                                                                    |           |
                                                               [InfluxDB]  [CSV Log]
                                                                    |
                                                              [Grafana Dashboard]
                                                              [Grafana Alerts]
```

## Components

### Edge Layer
- **Sensor Simulator** (`src/simulator/sensor_simulator.py`): Generates realistic machine telemetry (temperature, vibration, power) as if from physical sensors. Designed to be replaced by real Raspberry Pi GPIO reads.
- **Publisher** (`src/edge/publisher.py`): Reads simulator output and publishes JSON payloads to the MQTT broker.

### Message Broker
- **Mosquitto** (Docker): Lightweight MQTT broker that decouples edge devices from backend processing.

### Backend Layer
- **Subscriber** (`src/backend/subscriber.py`): Subscribes to MQTT topics, writes telemetry to InfluxDB, and logs alert events to CSV.
- **InfluxDB** (Docker): Time-series database storing all machine telemetry for historical analysis and alerting.

### Visualization Layer
- **Grafana** (Docker): Connects to InfluxDB via provisioned data source. Renders real-time dashboards and fires alerts when thresholds are exceeded.

## Alert Rules (Provisioned)

Stored in `grafana/provisioning/alerting/alert-rules.yml`:

| Alert | Threshold | Description |
|---|---|---|
| Temperature Threshold Exceeded | > 85 °C | Latest machine temperature is above 85 C. |
| Vibration Threshold Exceeded | > 7.5 mm/s | Latest machine vibration is above 7.5 mm/s. |
| Power Threshold Exceeded | > 12000 W | Latest machine power consumption is above 12000 W. |

All alerts evaluate every 30 seconds with a 30-second pending period and are grouped under the `Industrial IoT` folder.

## Data Flow

1. Simulator generates telemetry payload every N seconds (configurable via `PUBLISH_INTERVAL`).
2. Publisher serializes as JSON and publishes to `factory/machines/<machine_id>/telemetry`.
3. Subscriber receives message, writes to InfluxDB `machine_telemetry` measurement.
4. Subscriber checks thresholds; if exceeded, appends row to `data/alerts_log.csv`.
5. Grafana queries InfluxDB using Flux every 30s and fires alerts when thresholds are exceeded.

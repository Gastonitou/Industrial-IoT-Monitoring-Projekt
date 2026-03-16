# System Architecture

## Overview

The Industrial IoT Monitoring System follows a layered edge-to-cloud architecture:

```
[Sensors / Simulator]
        |
        v
[Raspberry Pi Edge Publisher]  ← runs src/edge/publisher.py
        |
       MQTT (paho-mqtt)
        |
        v
[Mosquitto MQTT Broker]  ← runs in Docker
        |
        v
[Backend Subscriber]  ← runs src/backend/subscriber.py
       / \
      /   \
     v     v
[InfluxDB]  [CSV Logs]
     |
     v
[Grafana Dashboard]
```

## Component Descriptions

### Sensor Simulator (`src/simulator/sensor_simulator.py`)
Generates realistic telemetry data for temperature, vibration, and power consumption. Designed to be replaced by real hardware sensor readings on a Raspberry Pi.

### Edge Publisher (`src/edge/publisher.py`)
Reads telemetry data and publishes it to the MQTT broker on the topic `factory/machines/<machine_id>/telemetry`. Runs on the Raspberry Pi or local machine.

### Mosquitto MQTT Broker
Lightweight message broker running in Docker. Handles all MQTT communication between edge devices and the backend.

### Backend Subscriber (`src/backend/subscriber.py`)
Subscribes to all machine telemetry topics, processes each message, writes data to InfluxDB, and logs alerts to CSV when thresholds are exceeded.

### InfluxDB
Time-series database optimized for IoT metrics. Stores all telemetry data for historical analysis.

### Grafana
Visualization platform connected to InfluxDB. Displays real-time and historical dashboards for machine monitoring.

## Data Flow

1. Simulator generates sensor readings every 5 seconds
2. Publisher serializes data to JSON and sends to MQTT broker
3. Subscriber receives JSON, checks alert thresholds, writes to InfluxDB
4. Grafana queries InfluxDB and refreshes panels automatically
5. Alert events are also written to `data/alerts_log.csv`

## MQTT Topic Structure

```
factory/machines/{machine_id}/telemetry
```

Example: `factory/machines/MACHINE-01/telemetry`

## Alert Thresholds

| Metric | Default Threshold |
|--------|------------------|
| Temperature | > 85 °C |
| Vibration | > 7.5 mm/s |
| Power | > 12 000 W |

Thresholds are configurable via `.env`.

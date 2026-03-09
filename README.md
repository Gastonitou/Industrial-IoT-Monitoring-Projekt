# 🏭 Industrial IoT Monitoring System

> **Real-time machine condition monitoring for factory floors**  
> Python · MQTT · InfluxDB · Grafana · Docker · Raspberry Pi

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto%202.0-orange?logo=eclipsemosquitto)](https://mosquitto.org/)
[![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-purple?logo=influxdb)](https://www.influxdata.com/)
[![Grafana](https://img.shields.io/badge/Grafana-10.2-yellow?logo=grafana)](https://grafana.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Features](#-features)
- [Architecture](#-architecture)
- [Folder Structure](#-folder-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Running on Raspberry Pi](#-running-on-raspberry-pi)
- [Grafana Dashboard](#-grafana-dashboard)
- [Alert System](#-alert-system)
- [MQTT Topic Structure](#-mqtt-topic-structure)
- [Development & Testing](#-development--testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Problem Statement

Factories often **cannot monitor machine conditions in real time**.  Undetected
temperature spikes, abnormal vibrations, and unexpected power surges lead to:

- Unplanned downtime and lost production
- Expensive reactive maintenance
- Safety incidents
- Higher energy costs

This project solves that by providing an **end-to-end Industrial IoT monitoring
pipeline** that collects sensor data at the edge, transports it over MQTT, stores
it in a time-series database, and visualises it on a live Grafana dashboard –
with an integrated alert system for out-of-range values.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📡 **Real-time monitoring** | Sensor readings every 5 seconds, streamed over MQTT |
| 🌡️ **Multi-sensor support** | Temperature (°C), Vibration (mm/s RMS), Power consumption (kW) |
| 🏭 **Multi-machine** | Configurable for any number of machines and locations |
| ⚠️ **Alert system** | WARNING and CRITICAL thresholds, log output + optional e-mail |
| 🗄️ **Data logging** | All readings persisted in InfluxDB time-series database |
| 📊 **Live dashboard** | Auto-provisioned Grafana dashboard with gauges, trends, and anomaly log |
| 🐳 **Docker Compose** | One-command deployment of the entire stack |
| 🍓 **Raspberry Pi ready** | Edge publisher runs on any Linux device |
| 🧪 **Tested** | Unit tests for simulator and alert logic |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FACTORY FLOOR (Edge)                            │
│                                                                     │
│  Physical Sensors → Raspberry Pi                                    │
│  (sensor_simulator.py + mqtt_publisher.py)                         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  MQTT  (TCP 1883)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  BACKEND / CLOUD                                     │
│                                                                     │
│  Mosquitto Broker → mqtt_subscriber.py → InfluxDB v2               │
│                              └──────────→ AlertManager             │
│                                                                     │
│  InfluxDB ──────────────────────────────→ Grafana Dashboard        │
└─────────────────────────────────────────────────────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full diagram and
data-flow description.

---

## 📁 Folder Structure

```
Industrial-IoT-Monitoring-Projekt/
├── docker-compose.yml          # Full stack: Mosquitto + InfluxDB + Grafana + subscriber
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
│
├── config/
│   └── config.yaml             # Machines, sensors, thresholds, MQTT, InfluxDB settings
│
├── edge/                       # Runs on Raspberry Pi / edge device
│   ├── sensor_simulator.py     # Generates realistic sensor readings
│   └── mqtt_publisher.py       # Publishes readings to MQTT broker
│
├── backend/                    # Runs on server / cloud
│   ├── mqtt_subscriber.py      # Consumes MQTT messages, writes to InfluxDB
│   ├── alert_manager.py        # WARNING/CRITICAL threshold evaluation
│   └── Dockerfile              # Container image for the subscriber service
│
├── broker/
│   └── mosquitto.conf          # Eclipse Mosquitto broker configuration
│
├── dashboard/
│   └── grafana/
│       ├── dashboards/
│       │   └── iot_dashboard.json          # Pre-built Grafana dashboard
│       └── provisioning/
│           ├── dashboards/dashboard.yml    # Auto-provision dashboards
│           └── datasources/influxdb.yml    # Auto-provision InfluxDB datasource
│
├── tests/
│   ├── test_sensor_simulator.py
│   └── test_alert_manager.py
│
└── docs/
    └── architecture.md         # Detailed system architecture
```

---

## 🛠 Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Docker](https://docs.docker.com/get-docker/) | 24+ | Container runtime |
| [Docker Compose](https://docs.docker.com/compose/install/) | v2+ | Stack orchestration |
| [Python](https://www.python.org/downloads/) | 3.11+ | Edge scripts / tests |

> **Raspberry Pi only:** Python 3.11 must be installed.  Docker is optional on
> the edge device — the publisher can run directly.

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Gastonitou/Industrial-IoT-Monitoring-Projekt.git
cd Industrial-IoT-Monitoring-Projekt
```

### 2. Create your environment file

```bash
cp .env.example .env
# Edit .env if you want to change credentials
```

### 3. Start the full stack

```bash
docker compose up -d
```

This starts:
- **Mosquitto** MQTT broker on port `1883` / `9001`
- **InfluxDB** on port `8086`
- **Grafana** on port `3000`
- **Subscriber** service (connects MQTT → InfluxDB)

### 4. Start the edge publisher (simulates sensor data)

```bash
pip install -r requirements.txt
python edge/mqtt_publisher.py
```

### 5. Open the dashboard

Navigate to **http://localhost:3000** → Login with `admin` / `admin`  
→ Browse to **Dashboards → IoT → Industrial IoT Monitoring**

---

## ⚙️ Configuration

All settings live in [`config/config.yaml`](config/config.yaml):

```yaml
mqtt:
  broker_host: "localhost"
  broker_port: 1883
  topic_prefix: "factory/machines"
  qos: 1

machines:
  - id: "machine_01"
    name: "CNC Lathe #1"
    location: "Hall A"
    sensors:
      - type: temperature
        normal_min: 20.0
        normal_max: 80.0
        alert_min: 10.0     # below this = CRITICAL alert
        alert_max: 95.0     # above this = CRITICAL alert

simulation:
  publish_interval_seconds: 5
  anomaly_probability: 0.05   # 5 % of readings will be anomalous
```

Environment variables (copy `.env.example` → `.env`) override YAML defaults
for secrets and deployment-specific values.

---

## 🍓 Running on Raspberry Pi

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set broker address (replace with your server IP)
export MQTT_BROKER_HOST=192.168.1.100

# Start the publisher
python edge/mqtt_publisher.py
```

To run as a systemd service, copy the following to
`/etc/systemd/system/iot-publisher.service` and enable it:

```ini
[Unit]
Description=Industrial IoT MQTT Publisher
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/Industrial-IoT-Monitoring-Projekt/edge/mqtt_publisher.py
WorkingDirectory=/home/pi/Industrial-IoT-Monitoring-Projekt
Restart=always
RestartSec=10
Environment=MQTT_BROKER_HOST=192.168.1.100

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable iot-publisher
sudo systemctl start iot-publisher
```

---

## 📊 Grafana Dashboard

The dashboard is automatically provisioned when you run `docker compose up`.

### Panels

| Panel | Type | Description |
|-------|------|-------------|
| **Temperature – All Machines** | Gauge | Latest temperature readings with colour thresholds |
| **Vibration – All Machines** | Gauge | Latest vibration readings |
| **Power Consumption – All Machines** | Gauge | Latest power readings |
| **Temperature Trend (1h)** | Time-series | 1-minute averages per machine |
| **Vibration Trend (1h)** | Time-series | 1-minute averages per machine |
| **Power Consumption Trend (1h)** | Time-series | 1-minute averages per machine |
| **Anomalies (last 1h)** | Stat | Count of anomaly events |
| **Recent Anomaly Events** | Table | Last 50 anomalous readings with details |

### Colour thresholds

| Sensor | Green | Yellow | Red |
|--------|-------|--------|-----|
| Temperature | < 70 °C | 70 – 90 °C | > 90 °C |
| Vibration | < 4.5 mm/s | 4.5 – 7.0 mm/s | > 7.0 mm/s |
| Power | < 15 kW | 15 – 20 kW | > 20 kW |

Dashboard auto-refreshes every **5 seconds**.

---

## ⚠️ Alert System

The `AlertManager` classifies each incoming reading against two thresholds:

| Level | Condition |
|-------|-----------|
| **OK** | Value within warning limits |
| **WARNING** | Value between warning and critical limits |
| **CRITICAL** | Value outside critical limits |

Warning limits are automatically set at the inner 90 % of the configured
`alert_min` / `alert_max` range.

### Enable e-mail alerts

Set these variables in your `.env`:

```dotenv
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.example.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_FROM=alerts@example.com
ALERT_EMAIL_TO=operator@example.com
ALERT_EMAIL_USERNAME=your_smtp_username
ALERT_EMAIL_PASSWORD=your_smtp_password
```

---

## 📨 MQTT Topic Structure

```
factory/machines/<machine_id>/<sensor_type>
```

Examples:
```
factory/machines/machine_01/temperature
factory/machines/machine_01/vibration
factory/machines/machine_01/power_consumption
factory/machines/machine_02/temperature
```

### Payload (JSON)

```json
{
  "machine_id":   "machine_01",
  "machine_name": "CNC Lathe #1",
  "location":     "Hall A",
  "sensor_type":  "temperature",
  "value":        54.327,
  "unit":         "°C",
  "timestamp":    1710031200.123,
  "is_anomaly":   false
}
```

---

## 🧪 Development & Testing

### Install dev dependencies

```bash
pip install -r requirements.txt
pip install pytest
```

### Run the tests

```bash
pytest tests/ -v
```

### Run sensor simulator in standalone mode (no MQTT)

```bash
python edge/sensor_simulator.py
```

### Useful Docker commands

```bash
# View logs
docker compose logs -f subscriber

# Access InfluxDB UI
open http://localhost:8086   # admin / adminpassword

# Access Grafana
open http://localhost:3000   # admin / admin

# Stop the stack
docker compose down

# Destroy all data
docker compose down -v
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
# System Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FACTORY FLOOR (Edge)                         │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │  CNC Lathe   │   │ Hydraulic    │   │  Conveyor Belt       │   │
│  │  machine_01  │   │ Press        │   │  machine_03          │   │
│  │              │   │ machine_02   │   │                      │   │
│  │ T | V | P    │   │ T | V | P    │   │ T | V | P            │   │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘   │
│         │                  │                        │               │
│         └──────────────────┴────────────────────────┘               │
│                            │                                         │
│                   ┌────────▼────────┐                               │
│                   │ Raspberry Pi    │                               │
│                   │ (Edge Device)   │                               │
│                   │                 │                               │
│                   │ sensor_        │                               │
│                   │ simulator.py   │                               │
│                   │ mqtt_          │                               │
│                   │ publisher.py   │                               │
│                   └────────┬────────┘                               │
└────────────────────────────│────────────────────────────────────────┘
                             │ MQTT (TCP 1883)
                             │ Topics: factory/machines/<id>/<sensor>
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CLOUD / ON-PREMISE SERVER                         │
│                                                                     │
│  ┌──────────────────────────────────────┐                          │
│  │      Eclipse Mosquitto (Broker)      │                          │
│  │           Port 1883 / 9001           │                          │
│  └──────────────────┬───────────────────┘                          │
│                     │ MQTT subscribe                                │
│                     ▼                                               │
│  ┌──────────────────────────────────────┐                          │
│  │      mqtt_subscriber.py              │                          │
│  │   (Python Backend Service)           │                          │
│  │                                      │                          │
│  │  ┌──────────────┐ ┌───────────────┐ │                          │
│  │  │ InfluxDB     │ │ AlertManager  │ │                          │
│  │  │ Writer       │ │               │ │                          │
│  │  └──────┬───────┘ └───────┬───────┘ │                          │
│  └─────────│─────────────────│─────────┘                          │
│            │ Write           │ Log / E-mail                        │
│            ▼                 ▼                                      │
│  ┌──────────────────┐   ┌──────────────────┐                      │
│  │   InfluxDB v2    │   │  Alert Log /     │                      │
│  │   Time-series DB │   │  SMTP Notifier   │                      │
│  │   Port 8086      │   │                  │                      │
│  └──────────────────┘   └──────────────────┘                      │
│            │                                                        │
│            │ Flux queries                                           │
│            ▼                                                        │
│  ┌──────────────────┐                                              │
│  │   Grafana 10     │                                              │
│  │   Dashboard      │                                              │
│  │   Port 3000      │                                              │
│  └──────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Sensor Simulator** (`edge/sensor_simulator.py`) generates synthetic
   readings for temperature (°C), vibration (mm/s RMS), and power
   consumption (kW) for each configured machine.

2. **MQTT Publisher** (`edge/mqtt_publisher.py`) serialises each reading
   as JSON and publishes to the broker on a structured topic:
   `factory/machines/<machine_id>/<sensor_type>`

3. **Eclipse Mosquitto** acts as the MQTT broker, routing messages
   between publishers (edge devices) and subscribers (backend services).

4. **MQTT Subscriber** (`backend/mqtt_subscriber.py`) consumes all
   sensor messages, writes them to InfluxDB, and passes them through
   the AlertManager.

5. **InfluxDB v2** stores all measurements as time-series data.  The
   `sensor_data` measurement uses the following schema:

   | Field / Tag  | Kind  | Description                         |
   |--------------|-------|-------------------------------------|
   | machine_id   | tag   | Unique machine identifier           |
   | machine_name | tag   | Human-readable name                 |
   | location     | tag   | Physical location (hall, line, etc.)|
   | sensor_type  | tag   | temperature / vibration / power_… |
   | is_anomaly   | tag   | "True" / "False"                    |
   | value        | field | Numeric measurement                 |
   | unit         | field | Engineering unit string             |

6. **Alert Manager** (`backend/alert_manager.py`) classifies each
   reading as OK / WARNING / CRITICAL and logs accordingly.  SMTP
   e-mail notifications can be enabled via environment variables.

7. **Grafana** visualises real-time and historical data through
   auto-provisioned dashboards.  The main dashboard includes:
   - Gauge panels (latest values per machine)
   - Time-series panels (1-hour trends)
   - Anomaly event log table

## Technology Stack

| Layer       | Technology             | Version |
|-------------|------------------------|---------|
| Edge device | Raspberry Pi OS / any  | –       |
| Simulation  | Python                 | 3.11+   |
| Messaging   | MQTT (paho-mqtt)       | 1.6.1   |
| Broker      | Eclipse Mosquitto      | 2.0     |
| Database    | InfluxDB               | 2.7     |
| Visualiz.   | Grafana                | 10.2    |
| Container.  | Docker / Compose       | 24+     |

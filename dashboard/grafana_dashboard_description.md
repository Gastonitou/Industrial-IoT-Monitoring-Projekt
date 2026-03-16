# Grafana Dashboard Specification

## Dashboard: Industrial IoT Overview

### Variables
- `machine_id`: query all distinct `machine_id` tag values from `machine_telemetry`

### Panels

#### 1. Temperature Trend
- **Type**: Time series
- **Query** (Flux):
```flux
from(bucket: "industrial-iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "machine_telemetry")
  |> filter(fn: (r) => r._field == "temperature_c")
  |> filter(fn: (r) => r.machine_id == "${machine_id}")
```
- **Thresholds**: Warning at 80 °C, Critical at 85 °C

#### 2. Vibration Trend
- **Type**: Time series
- **Query** (Flux):
```flux
from(bucket: "industrial-iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "machine_telemetry")
  |> filter(fn: (r) => r._field == "vibration_mm_s")
  |> filter(fn: (r) => r.machine_id == "${machine_id}")
```
- **Thresholds**: Warning at 6.5 mm/s, Critical at 7.5 mm/s

#### 3. Power Consumption Trend
- **Type**: Time series
- **Query** (Flux):
```flux
from(bucket: "industrial-iot")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "machine_telemetry")
  |> filter(fn: (r) => r._field == "power_w")
  |> filter(fn: (r) => r.machine_id == "${machine_id}")
```
- **Thresholds**: Warning at 11000 W, Critical at 12000 W

#### 4. Machine Status
- **Type**: Stat
- **Query** (Flux):
```flux
from(bucket: "industrial-iot")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "machine_telemetry")
  |> filter(fn: (r) => r._field == "temperature_c")
  |> filter(fn: (r) => r.machine_id == "${machine_id}")
  |> last()
  |> keep(columns: ["status"])
```

#### 5. Active Alerts Table
- **Type**: Table
- **Source**: Grafana Alerting — list all firing alerts for the `industrial-iot` project label

### Alert Rules
Alert rules are provisioned via `grafana/provisioning/alerting/alert-rules.yml`.

| Rule | Threshold | Pending | Interval |
|---|---|---|---|
| Temperature Threshold Exceeded | > 85 °C | 30s | 30s |
| Vibration Threshold Exceeded | > 7.5 mm/s | 30s | 30s |
| Power Threshold Exceeded | > 12000 W | 30s | 30s |

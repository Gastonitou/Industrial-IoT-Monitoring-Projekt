# Grafana Dashboard Specification

## Dashboard: Machine Overview

**Refresh interval:** 5s  
**Time range:** Last 1 hour (default)

### Panel 1 – Temperature Trend (Time Series)
- **Query:** `from(bucket: "iot_metrics") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "machine_telemetry" and r._field == "temperature_c")`
- **Unit:** °C
- **Alert threshold line:** 85 °C (red)

### Panel 2 – Vibration Trend (Time Series)
- **Query:** `from(bucket: "iot_metrics") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "machine_telemetry" and r._field == "vibration_mm_s")`
- **Unit:** mm/s
- **Alert threshold line:** 7.5 mm/s (orange)

### Panel 3 – Power Consumption Trend (Time Series)
- **Query:** `from(bucket: "iot_metrics") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "machine_telemetry" and r._field == "power_w")`
- **Unit:** W
- **Alert threshold line:** 12 000 W (yellow)

### Panel 4 – Machine Status (Stat Panel)
- **Query:**
  ```flux
  from(bucket: "iot_metrics")
    |> range(start: -5m)
    |> filter(fn: (r) => r._measurement == "machine_telemetry" and r._field == "status_code")
    |> group(columns: ["machine_id"])
    |> last()
  ```
- **Value mappings:** `0` → RUNNING (green), `1` → WARNING (yellow), `2` → ALERT (red)
- **Group by:** `machine_id` tag (one stat cell per machine)

### Panel 5 – Active Alerts Table
- **Source:** `data/alerts_log.csv` (or InfluxDB alerts measurement)
- **Columns:** Timestamp, Machine ID, Alert Type, Value

## Dashboard: 24h Trends

Same panels as above with `range(start: -24h)` for historical analysis.

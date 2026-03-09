"""
alert_manager.py
=================
Evaluates sensor readings against configured thresholds and triggers
alerts when values cross warning or critical limits.

Alerts are written to the application log and, optionally, dispatched
by e-mail via SMTP (controlled by environment variables).
"""

from __future__ import annotations

import logging
import os
import smtplib
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─── Alert levels ────────────────────────────────────────────────────────────────

class AlertLevel(Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ─── Data classes ────────────────────────────────────────────────────────────────

@dataclass
class AlertThreshold:
    """Thresholds for a single sensor on a machine."""
    sensor_type: str
    warning_min: float
    warning_max: float
    critical_min: float
    critical_max: float


@dataclass
class Alert:
    """Represents a triggered alert event."""
    machine_id: str
    machine_name: str
    sensor_type: str
    value: float
    unit: str
    level: AlertLevel
    message: str
    timestamp: float = field(default_factory=__import__("time").time)

    def to_dict(self) -> dict:
        return {
            "machine_id": self.machine_id,
            "machine_name": self.machine_name,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp,
        }


# ─── Alert Manager ───────────────────────────────────────────────────────────────

class AlertManager:
    """
    Evaluates readings against thresholds and emits alerts.

    Default thresholds are derived from the machine configs in ``config.yaml``
    (alert_min / alert_max map to *critical* limits; warning limits are set at
    90 % of the critical range by default).
    """

    def __init__(
        self,
        thresholds: Optional[Dict[str, List[AlertThreshold]]] = None,
        email_enabled: bool = False,
    ) -> None:
        # thresholds: { machine_id -> [AlertThreshold, …] }
        self._thresholds: Dict[str, List[AlertThreshold]] = thresholds or {}
        self._email_enabled = email_enabled

    # ── Public API ───────────────────────────────────────────────────────────────

    def evaluate(self, reading: dict) -> Optional[Alert]:
        """
        Evaluate a sensor reading dict (as produced by
        :meth:`SensorReading.to_dict`).

        Returns an :class:`Alert` if a threshold is breached, else ``None``.
        """
        machine_id = reading["machine_id"]
        sensor_type = reading["sensor_type"]
        value = reading["value"]

        thresholds = self._thresholds.get(machine_id, [])
        threshold = next((t for t in thresholds if t.sensor_type == sensor_type), None)
        if threshold is None:
            return None

        level = self._classify(value, threshold)
        if level == AlertLevel.OK:
            return None

        message = (
            f"[{level.value}] Machine '{reading['machine_name']}' – "
            f"{sensor_type} = {value:.3f} {reading['unit']} "
            f"(critical range: {threshold.critical_min}–{threshold.critical_max})"
        )

        alert = Alert(
            machine_id=machine_id,
            machine_name=reading["machine_name"],
            sensor_type=sensor_type,
            value=value,
            unit=reading["unit"],
            level=level,
            message=message,
            timestamp=reading.get("timestamp", __import__("time").time()),
        )

        self._log_alert(alert)
        if self._email_enabled:
            self._send_email(alert)

        return alert

    # ── Classification ───────────────────────────────────────────────────────────

    @staticmethod
    def _classify(value: float, threshold: AlertThreshold) -> AlertLevel:
        if value < threshold.critical_min or value > threshold.critical_max:
            return AlertLevel.CRITICAL
        if value < threshold.warning_min or value > threshold.warning_max:
            return AlertLevel.WARNING
        return AlertLevel.OK

    # ── Logging ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _log_alert(alert: Alert) -> None:
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(alert.message)
        else:
            logger.warning(alert.message)

    # ── E-mail notification ──────────────────────────────────────────────────────

    def _send_email(self, alert: Alert) -> None:
        smtp_host = os.getenv("ALERT_EMAIL_SMTP_HOST", "")
        smtp_port = int(os.getenv("ALERT_EMAIL_SMTP_PORT", "587"))
        from_addr = os.getenv("ALERT_EMAIL_FROM", "")
        to_addr = os.getenv("ALERT_EMAIL_TO", "")
        username = os.getenv("ALERT_EMAIL_USERNAME", "")
        password = os.getenv("ALERT_EMAIL_PASSWORD", "")

        if not (smtp_host and from_addr and to_addr):
            logger.debug("E-mail alert skipped – SMTP not fully configured.")
            return

        subject = f"[IoT Alert] {alert.level.value}: {alert.machine_name} – {alert.sensor_type}"
        body = (
            f"Alert Level : {alert.level.value}\n"
            f"Machine     : {alert.machine_name} ({alert.machine_id})\n"
            f"Sensor      : {alert.sensor_type}\n"
            f"Value       : {alert.value:.3f} {alert.unit}\n"
            f"Message     : {alert.message}\n"
        )

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                if username:
                    server.login(username, password)
                server.sendmail(from_addr, [to_addr], msg.as_string())
            logger.info("Alert e-mail sent to %s.", to_addr)
        except Exception as exc:
            logger.error("Failed to send alert e-mail: %s", exc)


# ─── Factory helper ──────────────────────────────────────────────────────────────

def build_alert_manager_from_config(config: dict) -> AlertManager:
    """
    Build an :class:`AlertManager` from a parsed ``config.yaml`` dict.

    The alert_min / alert_max values in each machine sensor config are used as
    *critical* limits.  Warning limits are set at the inner 90 % of that range.
    """
    thresholds: Dict[str, List[AlertThreshold]] = {}

    for machine in config.get("machines", []):
        machine_id = machine["id"]
        thresholds[machine_id] = []
        for sensor in machine.get("sensors", []):
            c_min = sensor["alert_min"]
            c_max = sensor["alert_max"]
            span = c_max - c_min
            w_min = c_min + span * 0.05
            w_max = c_max - span * 0.05
            thresholds[machine_id].append(
                AlertThreshold(
                    sensor_type=sensor["type"],
                    warning_min=w_min,
                    warning_max=w_max,
                    critical_min=c_min,
                    critical_max=c_max,
                )
            )

    email_enabled = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
    return AlertManager(thresholds=thresholds, email_enabled=email_enabled)

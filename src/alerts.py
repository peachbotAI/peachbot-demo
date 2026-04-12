# src/alerts.py
import threading
import datetime
from typing import Dict, List
from src.models import Doctor


class AlertManager:
    def __init__(self, doctors: Dict[str, Doctor]):
        self._lock = threading.Lock() # For thread safety
        self.doctors = doctors

        self.alerts = {}  # alert_id → alert
        self.active_index = {}  # (patient_id, issue) → alert_id

        self.counter = 1

    # =========================
    # LOGGING
    # =========================

    def log_alert(self, alert):
        with open("logs/alerts.log", "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            f.write(
                f"{timestamp} | {alert['id']} | {alert['patient_id']} | "
                f"{alert['severity']} | {alert['issue']} | {alert['assigned_to']} | {alert['status']}\n"
            )

    # =========================
    # CREATE ALERT ID
    # =========================
    def _generate_id(self):
        aid = f"ALERT-{self.counter:03d}"
        self.counter += 1
        return aid
    
    # =========================
    # GET ACTIVE ALERTS
    # =========================
    def get_active_alerts(self):
        with self._lock:
            return [
                a for a in self.alerts.values()
                if a["status"] == "ACTIVE"
            ]

    # =========================
    # DOCTOR ASSIGNMENT
    # =========================
    def assign_doctor(self, severity):
        for d in self.doctors.values():
            if severity == "CRITICAL" and d.role == "Intensivist":
                return d
            if severity == "WARNING" and d.role == "Medical Officer - General Duty":
                return d
        return None

    # =========================
    # INGEST ENGINE ALERTS
    # =========================
    def ingest(self, engine_alerts: List[dict]):
        with self._lock:
            new_alerts = []

            for alert in engine_alerts:

                # Ignore stable
                if alert["severity"] == "STABLE":
                    continue

                pid = alert["patient_id"]

                for issue in alert["issues"]:
                    key = (pid, issue)

                    # Deduplication
                    if key in self.active_index:
                        continue

                    doctor = self.assign_doctor(alert["severity"])

                    alert_id = self._generate_id()

                    new_alert = {
                        "id": alert_id,
                        "patient_id": pid,
                        "severity": alert["severity"],
                        "issue": issue,
                        "zone": alert["zone"],
                        "assigned_to": doctor.name if doctor else None,
                        "status": "ACTIVE"
                    }

                    self.alerts[alert_id] = new_alert
                    self.active_index[key] = alert_id

                    # Attach to doctor
                    if doctor:
                        doctor.active_alerts.append(alert_id)

                    new_alerts.append(new_alert)
                    self.log_alert(new_alert)

            return new_alerts

    # =========================
    # ACKNOWLEDGE
    # =========================
    def acknowledge(self, alert_id, doctor_id):
        with self._lock:
            if alert_id not in self.alerts:
                return False

            alert = self.alerts[alert_id]

            if alert["assigned_to"] != self.doctors[doctor_id].name:
                return False

            alert["status"] = "ACKNOWLEDGED"
            self.log_alert(alert)
            return True

    # =========================
    # OVERRIDE
    # =========================
    def override(self, alert_id, doctor_id, reason):
        with self._lock:
            if alert_id not in self.alerts:
                return False

            alert = self.alerts[alert_id]

            if alert["assigned_to"] != self.doctors[doctor_id].name:
                return False

            alert["status"] = "OVERRIDDEN"
            alert["override_reason"] = reason
            self.log_alert(alert)

            return True

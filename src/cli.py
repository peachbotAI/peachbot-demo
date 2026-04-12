# src/cli.py

import os


class CLIDashboard:
    def __init__(self, patients, alert_manager, doctors):
        self.patients = patients
        self.alert_manager = alert_manager
        self.doctors = doctors

    # =========================
    # CLEAR SCREEN
    # =========================
    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    # =========================
    # PATIENT TABLE
    # =========================
    def render_patients(self):
        print("=== PATIENTS ===")
        print("ID     | ZONE | HR | BP | TEMP")

        for p in list(self.patients.values())[:6]:
            v = p.vitals if p.vitals else {}

            print(
                f"{p.patient_id} | {p.zone or '-'}   | "
                f"{v.get('hr', '-')} | {v.get('bp', '-')} | {v.get('temp', '-')}"
            )

    # =========================
    # ALERT PANEL
    # =========================
    def render_alerts(self):
        print("\n=== ALERTS ===")

        alerts = self.alert_manager.get_active_alerts()

        if not alerts:
            print("No active alerts")
            return

        for a in alerts:
            print(
                f"{a['id']} | {a['patient_id']} | {a['severity']} | "
                f"{a['issue']} | {a['assigned_to']} | {a['status']}"
            )

    # =========================
    # COMMAND HANDLER
    # =========================
    def handle_command(self, cmd):
        parts = cmd.strip().split()

        if not parts:
            return

        if parts[0] == "ack" and len(parts) == 2:
            alert_id = parts[1]

            # find doctor automatically
            for d in self.doctors.values():
                if self.alert_manager.acknowledge(alert_id, d.doctor_id):
                    print(f"✔ {alert_id} acknowledged by {d.name}")
                    return

            print("✖ Failed to acknowledge")

        elif parts[0] == "override" and len(parts) >= 3:
            alert_id = parts[1]
            reason = " ".join(parts[2:])

            for d in self.doctors.values():
                if self.alert_manager.override(alert_id, d.doctor_id, reason):
                    print(f"⚠ {alert_id} overridden: {reason}")
                    return

            print("✖ Failed to override")

        else:
            print("Commands: ack <id> | override <id> <reason>")

    # =========================
    # MAIN RENDER
    # =========================
    def render(self):
        self.clear()
        self.render_patients()
        self.render_alerts()
        print("\nCommand: ", end="", flush=True)

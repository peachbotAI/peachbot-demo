from src.models import load_emr_data, load_doctors
from src.simulator import HL7Simulator
from src.engine import MonitoringEngine
from src.knowledge.rule_engine import RuleEngine   # NEW
from src.alerts import AlertManager
from src.gui import PeachBotGUI

import tkinter as tk
import threading
import time


if __name__ == "__main__":
    patients = load_emr_data()
    doctors = load_doctors()

    sim = HL7Simulator(patients)
    engine = MonitoringEngine(patients)
    rule_engine = RuleEngine()   # NEW
    alert_manager = AlertManager(doctors)

    # -------- BACKGROUND THREAD --------
    def monitoring_loop():
        while True:
            sim_output = sim.step()

            # -------------------------
            # 1. VITALS (MonitoringEngine)
            # -------------------------
            engine_alerts = engine.process(sim_output)

            # -------------------------
            # 2. CLINICAL (RuleEngine)
            # -------------------------
            for alert in engine_alerts:
                patient = patients[alert["patient_id"]]

                clinical_result = rule_engine.evaluate(
                    patient,
                    sim_output.get("ehr", [])
                )

                # MERGE ISSUES
                alert["issues"].extend(clinical_result.get("issues", []))
            

                # UPDATE SEVERITY
                if clinical_result.get("critical_flag"):
                    alert["severity"] = "CRITICAL"
                else:
                    # take max severity
                    if alert["severity"] == "STABLE" and clinical_result.get("score", 0) > 0:
                        alert["severity"] = "WARNING"

            # -------------------------
            # 3. ALERT MANAGER
            # -------------------------
            alert_manager.ingest(engine_alerts)

            time.sleep(1)

    thread = threading.Thread(target=monitoring_loop, daemon=True)
    thread.start()

    # -------- GUI THREAD --------
    root = tk.Tk()
    gui = PeachBotGUI(root, patients, alert_manager, doctors)

    gui.refresh()
    root.mainloop()
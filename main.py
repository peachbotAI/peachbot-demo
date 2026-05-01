from src.models import load_emr_data, load_doctors
from src.simulator import HL7Simulator
from src.engine import MonitoringEngine
from src.knowledge.rule_engine import RuleEngine
from src.alerts import AlertManager
from src.gui import PeachBotGUI
from src.ui.boot_screen import BootScreen   # 🔥 NEW
from src.emr.load_single import load_single_patient

import tkinter as tk
import threading
import time


if __name__ == "__main__":

    # =========================
    # LOAD CORE DATA (UNCHANGED)
    # =========================
    patients = load_emr_data()
    doctors = load_doctors()

    sim = HL7Simulator(patients)
    engine = MonitoringEngine(patients)
    rule_engine = RuleEngine()
    alert_manager = AlertManager(doctors)

    # =========================
    # BACKGROUND THREAD (UNCHANGED)
    # =========================
    def monitoring_loop():
        while True:
            sim_output = sim.step()

            # -------------------------
            # 1. VITALS
            # -------------------------
            engine_alerts = engine.process(sim_output)

            # -------------------------
            # 2. CLINICAL RULES
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
                    if alert["severity"] == "STABLE" and clinical_result.get("score", 0) > 0:
                        alert["severity"] = "WARNING"

            # -------------------------
            # 3. ALERT MANAGER
            # -------------------------
            alert_manager.ingest(engine_alerts)

            time.sleep(1)

    thread = threading.Thread(target=monitoring_loop, daemon=True)
    thread.start()

    def add_patient_to_system(file_path):
        patient = load_single_patient(file_path)

        patients[patient.patient_id] = patient

        # IMPORTANT: also register in simulator
        sim.patients[patient.patient_id] = patient

    # =========================
    # GUI + BOOT SCREEN
    # =========================
    root = tk.Tk()
    root.title("PeachBot Clinical Monitoring System")

    root.withdraw()  # hide main window during boot

    def launch_main_app():
        root.deiconify()

        gui = PeachBotGUI(root, patients, alert_manager, doctors)
        gui.rule_engine = rule_engine  # Pass rule engine to GUI for manual testing
        gui.refresh()

    # Boot screen
    boot = BootScreen(root, patients, doctors, rule_engine)
    boot.start(launch_main_app)

    root.mainloop()
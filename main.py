from src.models import load_emr_data, load_doctors
from src.simulator import HL7Simulator
from src.engine import MonitoringEngine
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
    alert_manager = AlertManager(doctors)

    # -------- BACKGROUND THREAD --------
    def monitoring_loop():
        while True:
            sim_output = sim.step()
            engine_alerts = engine.process(sim_output)
            alert_manager.ingest(engine_alerts)
            time.sleep(1)

    thread = threading.Thread(target=monitoring_loop, daemon=True)
    thread.start()

    # -------- GUI THREAD --------
    root = tk.Tk()
    gui = PeachBotGUI(root, patients, alert_manager, doctors)

    gui.refresh()
    root.mainloop()
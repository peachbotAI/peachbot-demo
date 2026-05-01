# src/ui/prescription_form.py

import tkinter as tk
from tkinter import ttk
import json
import os


# =========================
# DRUG → CLASS MAP
# =========================
DRUG_DB = {
    "Diclofenac": "NSAID",
    "Nimesulide": "NSAID",
    "Ibuprofen": "NSAID",
    "Atorvastatin": "STATIN",
    "Rosuvastatin": "STATIN",
    "Normal Saline": "FLUID"
}


class PrescriptionForm:
    def __init__(self, root, patient, rule_engine, alert_manager, refresh_callback, log_callback):
        self.root = root
        self.patient = patient
        self.rule_engine = rule_engine
        self.alert_manager = alert_manager
        self.refresh_callback = refresh_callback
        self.log_callback = log_callback

    def open(self):
        win = tk.Toplevel(self.root)
        win.title("FHIR Prescription")
        win.geometry("380x340")
        win.configure(bg="#0f172a")

        # =========================
        # TITLE
        # =========================
        tk.Label(
            win,
            text=f"Prescribe Drug → {self.patient.patient_id}",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 13, "bold")
        ).pack(pady=15)

        form = tk.Frame(win, bg="#0f172a")
        form.pack(padx=20, fill="x")

        # =========================
        # DRUG SELECT
        # =========================
        tk.Label(form, text="Select Drug", bg="#0f172a", fg="#94a3b8").pack(anchor="w")

        drug_var = tk.StringVar()

        drug_box = ttk.Combobox(
            form,
            textvariable=drug_var,
            values=list(DRUG_DB.keys()),
            state="readonly"
        )
        drug_box.pack(fill="x", pady=8)

        # =========================
        # INFO LABEL
        # =========================
        info_label = tk.Label(
            form,
            text="",
            bg="#0f172a",
            fg="#38bdf8",
            font=("Consolas", 10)
        )
        info_label.pack(pady=5)

        def on_select(event):
            drug = drug_var.get()
            d_class = DRUG_DB.get(drug, "UNKNOWN")
            info_label.config(text=f"Class: {d_class}")

        drug_box.bind("<<ComboboxSelected>>", on_select)

        # =========================
        # SUBMIT
        # =========================
        def submit():
            drug = drug_var.get()

            if not drug:
                return

            drug_class = DRUG_DB.get(drug, "UNKNOWN")

            # =========================
            # 1. FHIR (SIMULATED)
            # =========================
            fhir_request = {
                "resourceType": "MedicationRequest",
                "subject": {"reference": self.patient.patient_id},
                "medicationCodeableConcept": {
                    "text": drug
                },
                "category": drug_class
            }

            # =========================
            # 2. SAVE TO EMR (JSON)
            # =========================
            file_path = f"data/emr/{self.patient.patient_id}.json"

            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    bundle = json.load(f)
            else:
                bundle = {}

            # Create medication entry
            med_entry = {
                "name": drug,
                "generic": drug,
                "dose": "NA",
                "frequency": "NA",
                "class": drug_class,
                "source": "UI_PRESCRIPTION"
            }

            bundle.setdefault("medications", [])
            bundle["medications"].append(med_entry)

            with open(file_path, "w") as f:
                json.dump(bundle, f, indent=2)

            # =========================
            # 3. UPDATE IN-MEMORY PATIENT
            # =========================
            if not hasattr(self.patient, "medications"):
                self.patient.medications = []

            self.patient.medications.append(med_entry)

            # =========================
            # 4. CREATE EHR EVENT
            # =========================
            ehr_event = {
                "type": "EHR",
                "patient_id": self.patient.patient_id,
                "drug": drug,
                "class": drug_class
            }

            self.log_callback(
                f"PRESCRIBE {self.patient.patient_id} | {drug} ({drug_class})"
            )

            # =========================
            # 5. RUN RULE ENGINE
            # =========================
            result = self.rule_engine.evaluate(self.patient, [ehr_event])

            if result.get("issues"):
                alert = {
                    "patient_id": self.patient.patient_id,
                    "zone": self.patient.zone,
                    "severity": "CRITICAL" if result.get("critical_flag") else "WARNING",
                    "score": result.get("score", 0),
                    "vitals": {},
                    "issues": result["issues"]
                }

                self.alert_manager.ingest([alert])

    

            # =========================
            # 6. REFRESH UI
            # =========================
            self.refresh_callback()
            win.destroy()

        # =========================
        # BUTTON
        # =========================
        tk.Button(
            win,
            text="Prescribe",
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=10,
            pady=6,
            command=submit
        ).pack(pady=20)
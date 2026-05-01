# src/ui/patient_form.py

import tkinter as tk
from tkinter import ttk
import json

from src.emr.create_patient import create_patient_bundle
from src.emr.load_single import load_single_patient

CONDITION_MAP = {
    "HTN": "Hypertension",
    "CKD": "Chronic Kidney Disease",
    "CAD": "Coronary Artery Disease",
    "ASTHMA": "Asthma",
    "LIVER_DISEASE_ACTIVE": "Active Liver Disease",
    "DIABETES": "Diabetes Mellitus"
}


class PatientForm:
    def __init__(self, root, patients, refresh_callback):
        self.root = root
        self.patients = patients
        self.refresh_callback = refresh_callback

    def open(self):
        win = tk.Toplevel(self.root)
        win.title("Simulate Patient (FHIR)")
        win.geometry("380x420")
        win.configure(bg="#0f172a")

        # =========================
        # TITLE
        # =========================
        tk.Label(
            win,
            text="New Patient Registration",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=15)

        form = tk.Frame(win, bg="#0f172a")
        form.pack(padx=20, fill="x")

        # =========================
        # NAME
        # =========================
        tk.Label(form, text="Full Name", bg="#0f172a", fg="#94a3b8").pack(anchor="w")
        name_entry = tk.Entry(form, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=5)

        # =========================
        # AGE
        # =========================
        tk.Label(form, text="Age", bg="#0f172a", fg="#94a3b8").pack(anchor="w")
        age_entry = tk.Entry(form, font=("Segoe UI", 10))
        age_entry.pack(fill="x", pady=5)

        # =========================
        # GENDER
        # =========================
        tk.Label(form, text="Gender", bg="#0f172a", fg="#94a3b8").pack(anchor="w")

        gender_var = tk.StringVar(value="male")
        gender_box = ttk.Combobox(
            form,
            textvariable=gender_var,
            values=["male", "female", "other"],
            state="readonly"
        )
        gender_box.pack(fill="x", pady=5)

        # =========================
        # CONDITIONS
        # =========================
        tk.Label(form, text="Conditions", bg="#0f172a", fg="#94a3b8").pack(anchor="w")

        condition_list = tk.Listbox(
            form,
            selectmode="multiple",
            height=6,
            bg="#020617",
            fg="white",
            selectbackground="#2563eb",
            font=("Segoe UI", 10)
        )

        conditions = list(CONDITION_MAP.keys())

        for c in conditions:
            condition_list.insert(tk.END, CONDITION_MAP[c])

        condition_list.pack(fill="x", pady=5)

        # =========================
        # SUBMIT
        # =========================
        def submit():
            try:
                name = name_entry.get().strip()
                age = int(age_entry.get())
                gender = gender_var.get()

                selected_indices = condition_list.curselection()
                selected_conditions = [conditions[i] for i in selected_indices]

                # -------------------------
                # CREATE PATIENT
                # -------------------------
                bundle = create_patient_bundle(name, age, gender)

                pid = bundle["patient"]["id"]
                file_path = f"data/emr/{pid}.json"

                # -------------------------
                # ADD CONDITIONS
                # -------------------------
                bundle["conditions"] = [
                    {
                        "code": c,
                        "display": CONDITION_MAP.get(c, c)
                    }
                    for c in selected_conditions
                ]

                with open(file_path, "w") as f:
                    json.dump(bundle, f, indent=2)

                # -------------------------
                # LOAD INTO SYSTEM
                # -------------------------
                patient = load_single_patient(file_path)

                self.patients[patient.patient_id] = patient
                patient.zone = "OPD"

                self.refresh_callback()
                win.destroy()

            except Exception as e:
                print("Error creating patient:", e)

        tk.Button(
            win,
            text="Create Patient",
            bg="#22c55e",
            fg="black",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=10,
            pady=6,
            command=submit
        ).pack(pady=15)
# src/models.py

import json
import os
from typing import Dict, List

from src.config import DOCTORS


# =========================
# MODELS
# =========================

class Patient:
    def __init__(self, patient_id: str, name: str, age: int, gender: str):
        self.patient_id = patient_id
        self.name = name
        self.age = age
        self.gender = gender

        # Clinical data
        self.conditions: List[str] = []
        self.medications: List[dict] = []
        self.allergies: List[dict] = []

        # Vitals
        self.baseline_vitals = {}
        self.vitals = {}

        # System state
        self.zone = None  # OPD / OBS / HDU

    def __repr__(self):
        return f"<Patient {self.patient_id} {self.name}>"


class Doctor:
    def __init__(self, doctor_id: str, name: str, role: str):
        self.doctor_id = doctor_id
        self.name = name
        self.role = role

        # Runtime state
        self.active_alerts: List[dict] = []

    def __repr__(self):
        return f"<Doctor {self.doctor_id} {self.name} ({self.role})>"


# =========================
# LOADERS
# =========================

def load_doctors() -> Dict[str, Doctor]:
    doctors = {}

    for d in DOCTORS:
        doctor = Doctor(
            doctor_id=d["id"],
            name=d["name"],
            role=d["role"]
        )
        doctors[doctor.doctor_id] = doctor

    return doctors


def load_emr_data(emr_path: str = "data/emr") -> Dict[str, Patient]:
    patients = {}

    # Ensure folder exists
    if not os.path.exists(emr_path):
        print(f"[ERROR] EMR path not found: {emr_path}")
        return patients

    for file in sorted(os.listdir(emr_path)):
        if not file.endswith(".json"):
            continue

        full_path = os.path.join(emr_path, file)

        try:
            with open(full_path, "r") as f:
                data = json.load(f)

            # Validate structure
            if "patient" not in data:
                print(f"[WARN] Skipping invalid EMR file: {file}")
                continue

            p = data["patient"]

            patient = Patient(
                patient_id=p["id"],
                name=p["name"],
                age=p["age"],
                gender=p["gender"]
            )

            # Conditions
            patient.conditions = [
                c["code"] for c in data.get("conditions", [])
            ]

            # Medications (keep structured)
            patient.medications = data.get("medications", [])

            # Allergies (structured)
            patient.allergies = data.get("allergies", [])

            # Baseline vitals
            patient.baseline_vitals = data.get("baseline_vitals", {})

            patients[patient.patient_id] = patient

        except Exception as e:
            print(f"[ERROR] Failed loading {file}: {e}")

    return patients
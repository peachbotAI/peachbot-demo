import json
from src.models import Patient


def load_single_patient(file_path):

    with open(file_path, "r") as f:
        bundle = json.load(f)

    p = bundle["patient"]

    # -------------------------
    # CREATE PATIENT (ONLY VALID ARGS)
    # -------------------------
    patient = Patient(
        patient_id=p["id"],
        name=p.get("name", ""),
        age=p.get("age", 0),
        gender=p.get("gender", "")
    )

    # -------------------------
    # ADD EXTRA FIELDS (POST INIT)
    # -------------------------
    patient.conditions = [
        c["code"] if isinstance(c, dict) else c
        for c in bundle.get("conditions", [])
    ]

    patient.medications = bundle.get("medications", [])

    patient.zone = "OPD"

    patient.baseline_vitals = bundle.get("baseline_vitals", {
        "hr": 75,
        "bp": 120,
        "temp": 36.8
    })

    return patient
import os
import json


EMR_PATH = "data/emr"


def get_next_patient_id():
    files = [f for f in os.listdir(EMR_PATH) if f.startswith("PT-")]

    numbers = []
    for f in files:
        try:
            num = int(f.replace("PT-", "").replace(".json", ""))
            numbers.append(num)
        except:
            continue

    next_id = max(numbers) + 1 if numbers else 1
    return f"PT-{next_id:03d}"


def create_patient_bundle(name, age, gender):
    pid = get_next_patient_id()

    bundle = {
        "resourceType": "PatientBundle",
        "patient": {
            "id": pid,
            "name": name,
            "age": age,
            "gender": gender
        },
        "conditions": [],
        "medications": [],
        "encounters": [],
        "allergies": [],
        "baseline_vitals": {
            "hr": 75,
            "bp": 120,
            "temp": 36.8
        }
    }

    # Save to EMR
    file_path = os.path.join(EMR_PATH, f"{pid}.json")

    with open(file_path, "w") as f:
        json.dump(bundle, f, indent=2)

    return bundle
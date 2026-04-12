# src/config.py

MAX_PATIENTS = 10

OPD_LIMIT = 2
OBS_LIMIT = 5
HDU_LIMIT = 1

# Doctors with roles
DOCTORS = [
    {
        "id": "DR-001",
        "name": "Dr. A",
        "role": "Medical Officer - General Duty"
    },
    {
        "id": "DR-002",
        "name": "Dr. B",
        "role": "Intensivist"
    }
]

# Alert thresholds
HR_CRITICAL = 120
TEMP_CRITICAL = 38
BP_CRITICAL = 90

# Clinical rules
RULE_NSAID_CKD = "CRITICAL"
RULE_SALINE_HTN = "WARNING"

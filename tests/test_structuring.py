# tests/test_structuring.py

import pytest
from src.structuring.vitals_structurer import VitalsStructurer


def test_vitals_structuring():
    s = VitalsStructurer()

    raw = {
        "type": "VITALS",
        "patient_id": "PT-001",
        "vitals": {
            "hr": 80,
            "bp": 120,
            "temp": 37.0
        }
    }

    out = s.process(raw)

    assert out["type"] == "VITALS"
    assert out["patient_id"] == "PT-001"
    assert out["hr"] == 80
    assert out["bp"] == 120
    assert out["temp"] == 37.0


def test_ehr_structuring():
    s = VitalsStructurer()

    raw = {
        "type": "EHR",
        "patient_id": "PT-002",
        "drug": "Nimesulide",
        "class": "NSAID"
    }

    out = s.process(raw)

    assert out["type"] == "EHR"
    assert out["drug"] == "Nimesulide"
    assert out["drug_class"] == "NSAID"


def test_invalid_event_type():
    s = VitalsStructurer()

    raw = {
        "type": "UNKNOWN",
        "patient_id": "PT-001"
    }

    with pytest.raises(ValueError):
        s.process(raw)


def test_missing_patient_id():
    s = VitalsStructurer()

    raw = {
        "type": "VITALS",
        "vitals": {"hr": 80}
    }

    with pytest.raises(ValueError):
        s.process(raw)


def test_invalid_vitals_format():
    s = VitalsStructurer()

    raw = {
        "type": "VITALS",
        "patient_id": "PT-001",
        "vitals": "invalid"
    }

    with pytest.raises(ValueError):
        s.process(raw)
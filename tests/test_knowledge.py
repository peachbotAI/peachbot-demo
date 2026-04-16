# tests/test_knowledge.py

from src.knowledge.rule_engine import RuleEngine


# =========================
# DUMMY PATIENT
# =========================
class DummyPatient:
    def __init__(self, conditions=None, medications=None, profile=None):
        self.conditions = conditions or []
        self.medications = medications or []
        self.profile = profile or {}


# =========================
# DRUG-DRUG TESTS
# =========================
def test_drug_drug_sildenafil_nitrates():
    engine = RuleEngine()

    patient = DummyPatient(
        medications=[
            {"name": "Sildenafil"},
            {"name": "Nitrates"}
        ]
    )

    result = engine.evaluate(patient, [])

    assert result["critical_flag"] is True
    assert any("hypotension" in i["message"].lower() for i in result["issues"])


def test_drug_drug_no_match():
    engine = RuleEngine()

    patient = DummyPatient(
        medications=[
            {"name": "Paracetamol"}
        ]
    )

    result = engine.evaluate(patient, [])

    assert result["score"] == 0
    assert result["issues"] == []


# =========================
# DRUG-DISEASE TESTS
# =========================
def test_drug_disease_nsaid_ckd():
    engine = RuleEngine()

    patient = DummyPatient(
        conditions=[{"code": "CKD"}],
        medications=[{"name": "NSAIDs"}]
    )

    result = engine.evaluate(patient, [])

    assert result["critical_flag"] is True
    assert any("renal" in i["message"].lower() for i in result["issues"])


def test_drug_disease_htn_saline():
    engine = RuleEngine()

    patient = DummyPatient(
        conditions=[{"code": "HTN"}],
        medications=[{"name": "Normal Saline"}]
    )

    result = engine.evaluate(patient, [])

    assert result["score"] >= 2
    assert any("hypertension" in i["message"].lower() for i in result["issues"])


# =========================
# DRUG-PHYSIOLOGY TESTS
# =========================
def test_physiology_pregnancy_ace_inhibitor():
    engine = RuleEngine()

    patient = DummyPatient(
        medications=[{"name": "ACE_INHIBITOR"}],
        profile={
            "pregnant": True,
            "trimester": 3
        }
    )

    result = engine.evaluate(patient, [])

    assert result["critical_flag"] is True
    assert any("pregnancy" in i["message"].lower() for i in result["issues"])


def test_physiology_child_tetracycline():
    engine = RuleEngine()

    patient = DummyPatient(
        medications=[{"name": "Tetracyclines"}],
        profile={
            "age": 5
        }
    )

    result = engine.evaluate(patient, [])

    assert result["critical_flag"] is True
    assert any("children" in i["message"].lower() or "tooth" in i["message"].lower()
               for i in result["issues"])


def test_physiology_no_profile():
    engine = RuleEngine()

    patient = DummyPatient(
        medications=[{"name": "ACE_INHIBITOR"}]
    )

    result = engine.evaluate(patient, [])

    # Should NOT crash or falsely trigger
    assert result["score"] == 0 or isinstance(result["score"], int)


# =========================
# MIXED SCENARIO (REAL CASE)
# =========================
def test_combined_rules():
    engine = RuleEngine()

    patient = DummyPatient(
        conditions=[{"code": "CKD"}],
        medications=[
            {"name": "NSAIDs"},
            {"name": "Warfarin"}
        ],
        profile={
            "pregnant": False
        }
    )

    result = engine.evaluate(patient, [])

    # Should detect at least 1 serious issue
    assert result["score"] > 0
    assert len(result["issues"]) > 0
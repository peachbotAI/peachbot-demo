# tests/test_understanding.py

from src.understanding.vitals_analyzer import VitalsAnalyzer


def test_high_hr():
    analyzer = VitalsAnalyzer()

    event = {
        "type": "VITALS",
        "patient_id": "PT-001",
        "hr": 130,
        "bp": 120,
        "temp": 37
    }

    result = analyzer.analyze(event)

    assert result["score"] == 1
    assert "High HR" in result["issues"]


def test_multiple_issues():
    analyzer = VitalsAnalyzer()

    event = {
        "type": "VITALS",
        "patient_id": "PT-002",
        "hr": 130,
        "bp": 80,
        "temp": 39
    }

    result = analyzer.analyze(event)

    assert result["score"] == 3
    assert "High HR" in result["issues"]
    assert "Low BP" in result["issues"]
    assert "Fever" in result["issues"]


def test_normal_vitals():
    analyzer = VitalsAnalyzer()

    event = {
        "type": "VITALS",
        "patient_id": "PT-003",
        "hr": 80,
        "bp": 120,
        "temp": 37
    }

    result = analyzer.analyze(event)

    assert result["score"] == 0
    assert result["issues"] == []


def test_non_vitals_event():
    analyzer = VitalsAnalyzer()

    event = {
        "type": "EHR",
        "patient_id": "PT-004"
    }

    result = analyzer.analyze(event)

    assert result["score"] == 0
    assert result["issues"] == []

# tests/test_config.py

from src.config_loader import config


def test_thresholds_loaded():
    thresholds = config.load("thresholds.yaml")

    assert "vitals" in thresholds
    assert "hr" in thresholds["vitals"]
    assert "high" in thresholds["vitals"]["hr"]

def test_knowledge_rules_loaded():
    rules = config.load_all("knowledge")
    assert len(rules) > 0


def test_safety_config_loaded():
    safety = config.load("safety.yaml")

    assert "classification" in safety
    assert "CRITICAL" in safety["classification"]


def test_config_caching():
    first = config.load("thresholds.yaml")
    second = config.load("thresholds.yaml")

    assert first is second  # ensures caching works

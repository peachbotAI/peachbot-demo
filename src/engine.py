# src/engine.py

from typing import Dict
from src.models import Patient
from src.config import (
    HR_CRITICAL,
    TEMP_CRITICAL,
    BP_CRITICAL
)

from src.knowledge.rule_engine import RuleEngine


class MonitoringEngine:
    def __init__(self, patients: Dict[str, Patient]):
        self.patients = patients
        self.rule_engine = RuleEngine()

    # =========================
    # STRUCTURING
    # =========================
    def structure_vitals(self, raw_event):
        return {
            "patient_id": raw_event["patient_id"],
            "hr": raw_event["vitals"]["hr"],
            "bp": raw_event["vitals"]["bp"],
            "temp": raw_event["vitals"]["temp"]
        }
    
    # =========================
    # analyze_clinical 
    # =========================
    
    def analyze_clinical(self, patient, ehr_events):
        # USE RULE ENGINE (FINAL FIX)
        result = self.rule_engine.evaluate(patient, ehr_events)

        issues = result.get("issues", [])
        score = result.get("score", 0)
        critical_flag = result.get("critical_flag", False)

        return score, issues, critical_flag

    # =========================
    # UNDERSTANDING (Vitals)
    # =========================
    def analyze_vitals(self, data):
        score = 0
        issues = []

        if data["hr"] > HR_CRITICAL:
            score += 1
            issues.append("High HR")

        if data["temp"] > TEMP_CRITICAL:
            score += 1
            issues.append("Fever")

        if data["bp"] < BP_CRITICAL:
            score += 1
            issues.append("Low BP")

        return score, issues

    # =========================
    # CLASSIFICATION
    # =========================
    def classify(self, total_score):
        if total_score >= 3:
            return "CRITICAL"
        elif total_score == 2:
            return "WARNING"
        else:
            return "STABLE"

    # =========================
    # MAIN PROCESSOR
    # =========================
    def process(self, sim_output):
        alerts = []

        vitals_events = sim_output["vitals"]

        for raw in vitals_events:
            structured = self.structure_vitals(raw)

            patient = self.patients[structured["patient_id"]]

            ehr_events = sim_output["ehr"]   # 🔥 ADD THIS

            # -------------------------
            # VITALS
            # -------------------------
            v_score, v_issues = self.analyze_vitals(structured)

            # -------------------------
            # CLINICAL (RULE ENGINE)
            # -------------------------
            c_score, c_issues, critical_flag = self.analyze_clinical(
                patient, ehr_events
            )

            # -------------------------
            # COMBINE
            # -------------------------
            total_score = v_score + c_score

            if critical_flag:
                severity = "CRITICAL"
            else:
                severity = self.classify(total_score)

            # -------------------------
            # Convert to structured issues (IMPORTANT)
            # -------------------------
            structured_issues = []

            # Vitals issues
            for msg in v_issues:
                structured_issues.append({
                    "rule_id": "VITALS",
                    "type": "vitals",
                    "message": msg,
                    "severity": severity,
                    "risk": None,
                    "matched_entities": {},
                    "evidence": {}
                })

            # ADD clinical issues directly (already structured)
            structured_issues.extend(c_issues)

            alert = {
                "patient_id": patient.patient_id,
                "zone": patient.zone,
                "severity": severity,
                "score": v_score,
                "vitals": structured,
                "issues": structured_issues   # ALWAYS dict-based
            }

            alerts.append(alert)

        return alerts
# src/engine.py

from typing import Dict, List

from src.models import Patient
from src.config import (
    HR_CRITICAL,
    TEMP_CRITICAL,
    BP_CRITICAL
)


class MonitoringEngine:
    def __init__(self, patients: Dict[str, Patient]):
        self.patients = patients

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
    # KNOWLEDGE + CLINICAL RULES
    # =========================
    def analyze_clinical(self, patient: Patient, ehr_events: List[dict]):
        score = 0
        issues = []
        critical_flag = False

        for event in ehr_events:
            if event["patient_id"] != patient.patient_id:
                continue

            drug_class = event.get("class")

            # 🔴 NSAID + CKD → FORCE CRITICAL
            if drug_class == "NSAID" and "CKD" in patient.conditions:
                issues.append("NSAID in CKD")
                critical_flag = True

            # 🟡 Saline + HTN → WARNING
            if drug_class == "FLUID" and any(
                c in ["HTN", "HYPERTENSION"] for c in patient.conditions
            ):
                score += 2  # ensures WARNING
                issues.append("Saline in HTN")

        return score, issues, critical_flag

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
        ehr_events = sim_output["ehr"]

        for raw in vitals_events:
            structured = self.structure_vitals(raw)

            patient = self.patients[structured["patient_id"]]

            # Vitals analysis
            v_score, v_issues = self.analyze_vitals(structured)

            # Clinical analysis
            c_score, c_issues, critical_flag = self.analyze_clinical(
                patient, ehr_events
            )

            total_score = v_score + c_score

            # 🔥 Clinical override takes priority
            if critical_flag:
                severity = "CRITICAL"
            else:
                severity = self.classify(total_score)

            alert = {
                "patient_id": patient.patient_id,
                "zone": patient.zone,
                "severity": severity,
                "score": total_score,
                "vitals": structured,
                "issues": v_issues + c_issues
            }

            alerts.append(alert)

        return alerts
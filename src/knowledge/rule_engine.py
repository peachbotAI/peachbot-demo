# src/knowledge/rule_engine.py
import os
import yaml
from src.config_loader import config


class RuleEngine:
    """
    Enhanced Knowledge Engine
    Supports:
    - drug_drug
    - drug_disease
    - drug_physiology
    """

    def __init__(self):
        # Load all knowledge files
        self.rules = config.load_all("knowledge")

        # load ontology
        ontology_path = os.path.join(os.getcwd(), "knowledge", "ontology.yaml")

        if os.path.exists(ontology_path):
            with open(ontology_path, "r") as f:
                ontology = yaml.safe_load(f)
                self.drug_classes = ontology.get("drug_classes", {})
        else:
            self.drug_classes = {}

        self.rules = config.load_all("knowledge")


    def _normalize_drug(self, drug_name):
        """
        Normalize drug using ontology ONLY (no string hacks)
        """

        if not drug_name:
            return drug_name

        drug_name = drug_name.strip()

        # Check ontology mapping FIRST
        for class_name, drugs in self.drug_classes.items():

            # Match class directly
            if drug_name == class_name:
                return class_name

            # Match any synonym/member
            if drug_name in drugs:
                return class_name

        # If not found, return as-is
        return drug_name

    # =========================
    # MAIN ENTRY
    # =========================
    def evaluate(self, patient, structured_events: list):

        # -------------------------
        # EXTRACT
        # -------------------------
        patient_conditions = self._extract_conditions(patient)
        patient_drugs = self._extract_drugs(patient, structured_events)
        patient_profile = getattr(patient, "profile", {}) or {}


        # -------------------------
        # INIT
        # -------------------------
        issues = []
        total_score = 0
        critical_flag = False

        # -------------------------
        # MAIN RULE LOOP
        # -------------------------
        for rule in self.rules:

            rule_type = rule.get("type")
            entities = rule.get("entities", {})
            outcome = rule.get("outcome", {})

            matched = False

            # -------------------------
            # DRUG-DRUG
            # -------------------------
            if rule_type == "drug_drug":
                matched = self._match_drug_drug(rule, patient_drugs)

            # -------------------------
            # DRUG-DISEASE
            # -------------------------
            elif rule_type == "drug_disease":
                matched = self._match_drug_disease(
                    rule,
                    patient_conditions,
                    patient_drugs
                )

            # -------------------------
            # DRUG-PHYSIOLOGY
            # -------------------------
            elif rule_type == "drug_physiology":
                matched = self._match_drug_physiology(
                    rule,
                    patient_profile,
                    patient_drugs
                )

            # -------------------------
            # SKIP NON-MATCH
            # -------------------------
            if not matched:
                continue

            # -------------------------
            # RULE TRIGGERED
            # -------------------------
            severity = outcome.get("severity", "WARNING")
            score = outcome.get("score", 0)

            issues.append({
                "rule_id": rule.get("id"),
                "type": rule_type,

                # clinical
                "message": outcome.get("message"),
                "risk": outcome.get("risk"),
                "severity": severity,

                # explainability
                "matched_entities": entities,
                "normalized_drugs": list(patient_drugs),
                "conditions": patient_conditions,

                # evidence
                "evidence": rule.get("evidence", {})
            })

            total_score += score

            # CRITICAL PROPAGATION (IMPORTANT)
            if severity == "CRITICAL":
                critical_flag = True

        # -------------------------
        # FINAL OUTPUT
        # -------------------------
        return {
            "score": total_score,
            "issues": issues,
            "critical_flag": critical_flag
        }

    # =========================
    # MATCHERS
    # =========================

    def _match_drug_drug(self, rule, drugs):
        a = self._normalize_drug(rule["entities"]["drug_a"]["name"])
        b = self._normalize_drug(rule["entities"]["drug_b"]["name"])
        return a in drugs and b in drugs

    def _match_drug_disease(self, rule, conditions, drugs):
        cond = rule["entities"]["condition"].strip().upper()

        # DO NOT over-normalize rule drug
        drug = rule["entities"]["drug"].strip().upper()

        # Normalize patient conditions
        conditions = [c.strip().upper() for c in conditions]

        # Normalize drugs set (safety)
        drugs = {d.strip().upper() for d in drugs}

        # DEBUG (temporary)
        # print("MATCH CHECK →", cond, drug, "|", conditions, drugs)

        return cond in conditions and drug in drugs

    def _match_drug_physiology(self, rule, profile, drugs):

        cond = rule["entities"]["condition"]
        drug = rule["entities"]["drug"]

        # Drug must be present
        if drug not in drugs:
            return False

        # Map physiology conditions → profile keys
        return self._check_physiology(cond, profile)

    # =========================
    # PHYSIOLOGY LOGIC
    # =========================

    def _check_physiology(self, condition, profile):

        if not profile:
            return False

        # Pregnancy
        if condition == "PREGNANCY":
            return profile.get("pregnant") is True

        if condition == "PREGNANCY_FIRST_TRIMESTER":
            return profile.get("pregnant") and profile.get("trimester") == 1

        if condition == "PREGNANCY_2_3_TRIMESTER":
            return profile.get("pregnant") and profile.get("trimester") in [2, 3]

        # Age
        if condition == "CHILD_UNDER_8":
            return profile.get("age", 100) < 8

        # Immunity
        if condition == "IMMUNOCOMPROMISED":
            return profile.get("immunocompromised") is True

        # Genetics
        if condition == "ULTRA_RAPID_METABOLIZER":
            return profile.get("cyp2d6") == "ultra_rapid"

        # Sleep
        if condition == "SLEEP_APNEA":
            return profile.get("sleep_apnea") is True

        # Female reproductive
        if condition == "FEMALE_CHILDBEARING_AGE":
            return profile.get("female") and 15 <= profile.get("age", 0) <= 45

        return False

    # =========================
    # HELPERS
    # =========================

    def _extract_conditions(self, patient):
        conditions = []

        for c in getattr(patient, "conditions", []):
            if isinstance(c, dict):
                code = c.get("code")
                if code:
                    conditions.append(code.upper())   # USE CODE
            else:
                conditions.append(str(c).upper())

        return conditions

    def _extract_drugs(self, patient, events):
        drugs = set()

        # -------------------------
        # EMR meds
        # -------------------------
        if hasattr(patient, "medications"):
            for m in patient.medications:
                if isinstance(m, dict):
                    name = m.get("name")
                    if name:
                        drugs.add(self._normalize_drug(name))

        # -------------------------
        # EHR events (FIXED)
        # -------------------------
        for e in events:
            if e.get("type") != "EHR":
                continue

            if e.get("patient_id") != patient.patient_id:
                continue

            # ALWAYS add class if present
            drug_class = e.get("class")
            if drug_class:
                drugs.add(drug_class.strip().upper())

            # ALSO add normalized drug name
            drug_name = e.get("drug")
            if drug_name:
                drugs.add(self._normalize_drug(drug_name))

        # DEBUG
        # print(f"FINAL DRUG SET ({patient.patient_id}):", drugs)

        return drugs

        # EHR events
        for e in events:
            if e.get("type") == "EHR" and e.get("patient_id") == patient.patient_id:

                if e.get("class"):
                    drugs.add(e["class"].upper())
                    continue

                drug = e.get("drug")
                if drug:
                    drugs.add(self._normalize_drug(drug))

        return drugs
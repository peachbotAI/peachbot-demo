# src/understanding/vitals_analyzer.py

from src.config_loader import config


class VitalsAnalyzer:
    """
    Understanding Layer
    ------------------
    Interprets structured vitals using config thresholds
    Produces:
        - score
        - issues list
    """

    def __init__(self):
        self.thresholds = config.load("thresholds.yaml")["vitals"]

    def analyze(self, structured_event: dict) -> dict:
        """
        Input (from structuring layer):
        {
            "type": "VITALS",
            "patient_id": "PT-001",
            "hr": 130,
            "bp": 85,
            "temp": 39
        }

        Output:
        {
            "patient_id": "...",
            "score": 2,
            "issues": ["High HR", "Fever"]
        }
        """

        if structured_event.get("type") != "VITALS":
            return {
                "patient_id": structured_event.get("patient_id"),
                "score": 0,
                "issues": []
            }

        hr = structured_event.get("hr")
        bp = structured_event.get("bp")
        temp = structured_event.get("temp")

        score = 0
        issues = []

        # ---- HR ----
        if hr is not None and hr > self.thresholds["hr"]["high"]:
            score += 1
            issues.append("High HR")

        # ---- TEMP ----
        if temp is not None and temp > self.thresholds["temp"]["high"]:
            score += 1
            issues.append("Fever")

        # ---- BP ----
        if bp is not None and bp < self.thresholds["bp"]["low"]:
            score += 1
            issues.append("Low BP")

        return {
            "patient_id": structured_event["patient_id"],
            "score": score,
            "issues": issues
        }

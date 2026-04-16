# src/structuring/vitals_structurer.py

class VitalsStructurer:
    """
    Structuring Layer
    -----------------
    Converts raw simulator/HL7-like input into a normalized format.

    IMPORTANT:
    - No clinical logic
    - No thresholds
    - No scoring
    - Only data transformation
    """

    def process(self, raw_event: dict) -> dict:
        """
        Entry point for all events
        """

        if not isinstance(raw_event, dict):
            raise ValueError("Invalid event: must be dict")

        event_type = raw_event.get("type")

        if event_type == "VITALS":
            return self._process_vitals(raw_event)

        elif event_type == "EHR":
            return self._process_ehr(raw_event)

        else:
            raise ValueError(f"Unknown event type: {event_type}")

    # =========================
    # VITALS TRANSFORMATION
    # =========================
    def _process_vitals(self, raw_event: dict) -> dict:

        if "patient_id" not in raw_event:
            raise ValueError("Missing patient_id")

        vitals = raw_event.get("vitals")

        if not isinstance(vitals, dict):
            raise ValueError("Vitals must be a dictionary")

        return {
            "type": "VITALS",
            "patient_id": raw_event["patient_id"],
            "hr": vitals.get("hr"),
            "bp": vitals.get("bp"),
            "temp": vitals.get("temp"),
        }

    # =========================
    # EHR TRANSFORMATION
    # =========================
    def _process_ehr(self, raw_event: dict) -> dict:

        if "patient_id" not in raw_event:
            raise ValueError("Missing patient_id")

        return {
            "type": "EHR",
            "patient_id": raw_event["patient_id"],
            "drug": raw_event.get("drug"),
            "drug_class": raw_event.get("class"),
        }
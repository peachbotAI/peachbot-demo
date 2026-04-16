# src/simulator.py

import time
from typing import Dict, List

from src.models import Patient
from src.config import OPD_LIMIT, OBS_LIMIT, HDU_LIMIT


class HL7Simulator:
    def __init__(self, patients: Dict[str, Patient]):
        self.patients = patients

        # Deterministic index counters
        self.tick = 0
        self.patient_ids = sorted(list(patients.keys()))

        # Zone allocation
        self.opd: List[str] = []
        self.obs: List[str] = []
        self.hdu: List[str] = []

        self._initialize_zones()

    # =========================
    # INITIAL SETUP
    # =========================
    def _initialize_zones(self):
        ids = self.patient_ids

        self.opd = ids[:OPD_LIMIT]
        self.obs = ids[OPD_LIMIT:OPD_LIMIT + OBS_LIMIT]
        self.hdu = ids[OPD_LIMIT + OBS_LIMIT:OPD_LIMIT + OBS_LIMIT + HDU_LIMIT]

        for pid in self.opd:
            self.patients[pid].zone = "OPD"

        for pid in self.obs:
            self.patients[pid].zone = "OBS"

        for pid in self.hdu:
            self.patients[pid].zone = "HDU"

    # =========================
    # VITALS GENERATOR
    # =========================
    def generate_vitals(self, patient: Patient):
        base = patient.baseline_vitals

        # Deterministic variation using tick
        hr = base.get("hr", 70) + (self.tick % 5)
        bp = base.get("bp", 120) - (self.tick % 3)
        temp = base.get("temp", 36.5) + ((self.tick % 4) * 0.2)

        patient.vitals = {
            "hr": hr,
            "bp": bp,
            "temp": round(temp, 1)
        }

    # =========================
    # HIS EVENTS (OPD ROTATION)
    # =========================
    def rotate_opd(self):
        # Every 3 ticks rotate one patient
        if self.tick % 3 != 0:
            return None

        if not self.opd:
            return None

        discharged = self.opd.pop(0)
        self.patients[discharged].zone = None

        # Find next available patient not already in zones
        for pid in self.patient_ids:
            if pid not in self.opd and pid not in self.obs and pid not in self.hdu:
                self.opd.append(pid)
                self.patients[pid].zone = "OPD"
                return {
                    "type": "HIS",
                    "event": "ADMISSION",
                    "patient_id": pid
                }

        return {
            "type": "HIS",
            "event": "DISCHARGE",
            "patient_id": discharged
        }

    # =========================
    # EHR EVENTS (WRONG RX)
    # =========================
    def generate_ehr_events(self):
        events = []

        for pid, patient in self.patients.items():

            # -------------------------
            # NORMALIZE CONDITIONS (CRITICAL FIX)
            # -------------------------
            conditions = [
                c["code"] if isinstance(c, dict) else c
                for c in patient.conditions
            ]

            # Deterministic trigger
            if self.tick % 5 == 0:

                # -------------------------
                # CKD → NSAID (ADR)
                # -------------------------
                if "CKD" in conditions:
                    drug = "Nimesulide" if self.tick % 2 == 0 else "Diclofenac Sodium"

                    events.append({
                        "type": "EHR",
                        "patient_id": pid,
                        "drug": drug,
                        "class": "NSAID"
                    })

                # -------------------------
                # HTN → FLUID
                # -------------------------
                if "HTN" in conditions:
                    events.append({
                        "type": "EHR",
                        "patient_id": pid,
                        "drug": "Normal Saline",
                        "class": "FLUID"
                    })

                # -------------------------
                # LIVER DISEASE → STATIN (ADR)
                # -------------------------
                if "LIVER_DISEASE_ACTIVE" in conditions:
                    events.append({
                        "type": "EHR",
                        "patient_id": pid,
                        "drug": "Atorvastatin",
                        "class": "STATIN"
                    })

        return events

    # =========================
    # MAIN TICK LOOP
    # =========================
    def step(self):
        self.tick += 1

        vitals_output = []
        for patient in self.patients.values():
            self.generate_vitals(patient)

            vitals_output.append({
                "type": "HL7",
                "patient_id": patient.patient_id,
                "vitals": patient.vitals
            })

        his_event = self.rotate_opd()
        ehr_events = self.generate_ehr_events()

        return {
            "vitals": vitals_output,
            "his": his_event,
            "ehr": ehr_events
        }

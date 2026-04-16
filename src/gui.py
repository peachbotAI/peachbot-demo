# src/gui.py

import tkinter as tk
from tkinter import ttk, messagebox
from src.utils.explain import format_issue
import threading
import sys
import datetime


class PeachBotGUI:
    def __init__(self, root, patients, alert_manager, doctors):
        self.root = root
        self.patients = patients
        self.alert_manager = alert_manager
        self.doctors = doctors

        self.root.title("PeachBot ICU Monitor")
        self.root.geometry("800x480")
        self.root.minsize(800, 480)

        self.flash_state = False

        self.setup_ui()
    # =========================
    # ALERT EXPLANATION
    # =========================

    def update_explain(self):
        selected = self.alert_table.selection()

        if not selected:
            self.explain_box.delete("1.0", tk.END)
            self.explain_box.insert("end", "Select an alert to view clinical reasoning.")
            return

        alert_id = selected[0]
        alert = self.alert_manager.alerts.get(alert_id)

        if not alert:
            return

        # Build explanation
        explanation = []

        explanation.append(f"Patient: {alert['patient_id']}")
        explanation.append(f"Severity: {alert['severity']}")
        explanation.append("")
        explanation.append("Reason:")

        issues = alert.get("issues", [])

        if not issues:
            explanation.append("- No reasoning available")
        else:
            for i in issues:
                try:
                    explanation.append(f"- {format_issue(i)}")
                except Exception:
                    explanation.append(f"- {str(i)}")

        explanation.append("")
        explanation.append("System Logic:")
        explanation.append("- Input → Structuring → Clinical Rules → Alert")

        # render
        self.explain_box.delete("1.0", tk.END)
        self.explain_box.insert("end", "\n".join(explanation))
    # =========================
    # UI SETUP
    # =========================

    def setup_ui(self):

        self.root.configure(bg="#0b1220")

        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#0f172a",
            foreground="white",
            fieldbackground="#0f172a",
            rowheight=26,
            font=("Segoe UI", 9)
        )

        style.configure(
            "Treeview.Heading",
            background="#1e293b",
            foreground="white",
            font=("Segoe UI", 9, "bold")
        )

        style.map("Treeview",
                  background=[("selected", "#2563eb")],
                  foreground=[("selected", "white")])

        # =========================
        # ROOT GRID (2/3 : 1/3)
        # =========================
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=1)

        # =========================
        # LEFT PANEL
        # =========================
        left = tk.Frame(self.root, bg="#0b1220")
        left.grid(row=0, column=0, sticky="nsew")

        left.grid_rowconfigure(0, weight=1)  # patients
        left.grid_rowconfigure(1, weight=3)  # alerts
        left.grid_rowconfigure(2, weight=0)  # buttons
        left.grid_columnconfigure(0, weight=1)

        # -------- TOP (Patients + Doctors)
        top = tk.Frame(left, bg="#0b1220")
        top.grid(row=0, column=0, sticky="nsew", padx=5, pady=3)

        top.grid_columnconfigure(0, weight=3)
        top.grid_columnconfigure(1, weight=1)
        top.grid_rowconfigure(0, weight=1)

        # PATIENTS
        patient_card = tk.Frame(top, bg="#111827")
        patient_card.grid(row=0, column=0, sticky="nsew", padx=3)

        tk.Label(patient_card, text="Patients",
                 fg="white", bg="#111827",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=5)

        self.patient_table = ttk.Treeview(
            patient_card,
            columns=("zone", "hr", "bp", "temp"),
            show="headings",
            height=5
        )

        for col in ("zone", "hr", "bp", "temp"):
            self.patient_table.heading(col, text=col.upper())
            self.patient_table.column(col, anchor="center", width=70)

        self.patient_table.pack(fill="both", expand=True, padx=5, pady=3)

        # DOCTORS
        doctor_card = tk.Frame(top, bg="#111827")
        doctor_card.grid(row=0, column=1, sticky="nsew", padx=3)

        tk.Label(doctor_card, text="Doctors",
                 fg="white", bg="#111827",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=5)

        self.doctor_box = tk.Listbox(
            doctor_card,
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 9)
        )
        self.doctor_box.pack(fill="both", expand=True, padx=5, pady=3)

        self.update_doctors()

        # -------- ALERTS
        alert_card = tk.Frame(left, bg="#111827")
        alert_card.grid(row=1, column=0, sticky="nsew", padx=5, pady=3)

        alert_card.grid_rowconfigure(1, weight=1)
        alert_card.grid_columnconfigure(0, weight=1)

        tk.Label(alert_card, text="Clinical Alerts",
                 fg="white", bg="#111827",
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", padx=5)

        self.alert_table = ttk.Treeview(
            alert_card,
            columns=("patient", "severity", "issue", "doctor", "status"),
            show="headings"
        )

        for col in ("patient", "severity", "issue", "doctor", "status"):
            self.alert_table.heading(col, text=col.upper())
            self.alert_table.column(col, anchor="center", width=120)

        self.alert_table.tag_configure("CRITICAL", background="#b91c1c")
        self.alert_table.tag_configure("WARNING", background="#f59e0b")

        self.alert_table.grid(row=1, column=0, sticky="nsew", padx=5, pady=3)

        # -------- BUTTONS
        btn_bar = tk.Frame(left, bg="#0b1220")
        btn_bar.grid(row=2, column=0, sticky="ew", pady=5)

        tk.Button(btn_bar, text="Acknowledge",
                  command=self.ack_selected,
                  bg="#16a34a", fg="white",
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)

        tk.Button(btn_bar, text="Override",
                  command=self.override_selected,
                  bg="#dc2626", fg="white",
                  font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)

        # =========================
        # RIGHT PANEL (LOG + REASON)
        # =========================
        right = tk.Frame(self.root, bg="#0b1220")
        right.grid(row=0, column=1, sticky="nsew", padx=5, pady=3)

        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # LOG
        log_card = tk.Frame(right, bg="#111827")
        log_card.grid(row=0, column=0, sticky="nsew", pady=3)

        log_card.grid_rowconfigure(1, weight=1)

        tk.Label(log_card, text="Activity Log",
                 fg="white", bg="#111827",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)

        self.log_box = tk.Text(
            log_card,
            bg="#020617",
            fg="#22c55e",
            font=("Consolas", 9)
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=3)

        # EXPLAIN
        explain_card = tk.Frame(right, bg="#111827")
        explain_card.grid(row=1, column=0, sticky="nsew", pady=3)

        explain_card.grid_rowconfigure(1, weight=1)

        tk.Label(explain_card, text="Clinical Reasoning",
                 fg="white", bg="#111827",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)

        self.explain_box = tk.Text(
            explain_card,
            bg="#020617",
            fg="#38bdf8",
            font=("Consolas", 9)
        )
        self.explain_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=3)
    # =========================
    def update_doctors(self):
        self.doctor_box.delete(0, tk.END)
        for d in self.doctors.values():
            self.doctor_box.insert(tk.END, f"{d.name} ({d.role})")

    # =========================
    def log_action(self, msg):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"{timestamp} | {msg}\n")
        self.log_box.see("end")

    # =========================
    def get_reason_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Override Reason")
        popup.geometry("300x150")
        popup.configure(bg="#0f172a")
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Enter clinical reason:",
                 bg="#0f172a", fg="white").pack(pady=10)

        entry = tk.Entry(popup)
        entry.pack(pady=5)

        result = {"value": None}

        def submit():
            result["value"] = entry.get()
            popup.destroy()

        tk.Button(popup, text="Submit",
                  command=submit,
                  bg="#2563eb", fg="white").pack(pady=10)

        popup.wait_window()
        return result["value"]

    # =========================
    def update_patients(self):
        self.patient_table.delete(*self.patient_table.get_children())

        for p in list(self.patients.values())[:6]:
            v = p.vitals if p.vitals else {}

            self.patient_table.insert(
                "",
                "end",
                values=(p.zone, v.get("hr"), v.get("bp"), v.get("temp"))
            )

    # =========================
    def update_alerts(self):
        current_selection = self.alert_table.selection()
        self.alert_table.delete(*self.alert_table.get_children())

        alerts = self.alert_manager.get_active_alerts()
        critical_found = False

        for a in alerts:
            tag = a["severity"]

            if a["severity"] == "CRITICAL":
                critical_found = True

                # FLASH EFFECT
                if self.flash_state:
                    tag = "CRITICAL"
                else:
                    tag = ""  # remove color → blinking

            issues = a.get("issues", [])
            text = format_issue(issues[0]) if issues else ""

            self.alert_table.insert(
                "",
                "end",
                iid=a["id"],
                values=(
                    a["patient_id"],
                    "⚠ " + a["severity"],
                    text,
                    a["assigned_to"],
                    a["status"]
                ),
                tags=(tag,)
            )

        # restore selection
        for sel in current_selection:
            if sel in self.alert_table.get_children():
                self.alert_table.selection_add(sel)

        # sound only when new critical appears
        if critical_found:
            threading.Thread(target=self.play_alert_sound, daemon=True).start()

        # toggle flash
        self.flash_state = not self.flash_state

    # =========================
    def play_alert_sound(self):
        try:
            if sys.platform == "win32":
                import winsound
                winsound.Beep(1000, 400)
        except:
            pass

    # =========================
    def ack_selected(self):
        selected = self.alert_table.selection()

        if not selected:
            messagebox.showwarning("Warning", "No alert selected")
            return

        alert_id = selected[0]

        for d in self.doctors.values():
            if self.alert_manager.acknowledge(alert_id, d.doctor_id):
                self.log_action(f"ACK {alert_id}")
                break

    # =========================
    def override_selected(self):
        selected = self.alert_table.selection()

        if not selected:
            messagebox.showwarning("Warning", "No alert selected")
            return

        alert_id = selected[0]

        reason = self.get_reason_popup()

        if not reason:
            messagebox.showwarning("Required", "Reason is mandatory")
            return

        for d in self.doctors.values():
            if self.alert_manager.override(alert_id, d.doctor_id, reason):
                self.log_action(f"OVERRIDE {alert_id} | {reason}")
                break

    # =========================
    def refresh(self):
        self.update_patients()
        self.update_alerts()
        self.update_explain()
        self.root.after(1000, self.refresh)
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


class BootScreen:
    def __init__(self, root, patients, doctors, rule_engine):
        self.root = root
        self.patients = patients
        self.doctors = doctors
        self.rule_engine = rule_engine

        # =========================
        # WINDOW (8-INCH MODE)
        # =========================
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)

        width = 1024
        height = 600

        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()

        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)

        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg="#0f172a")

        # =========================
        # TOP (LOGO + STATUS)
        # =========================
        top = tk.Frame(self.window, bg="#0f172a")
        top.pack(pady=15)

        # LOGO
        try:
            img = Image.open("assets/logo.png")
            img.thumbnail((160, 160), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)

            tk.Label(top, image=self.logo, bg="#0f172a").pack()
        except Exception as e:
            print("Logo load error:", e)
            tk.Label(
                top,
                text="PEACHBOT",
                fg="white",
                bg="#0f172a",
                font=("Segoe UI", 22, "bold")
            ).pack()

        # TITLE
        tk.Label(
            top,
            text="Clinical Monitoring System",
            fg="#94a3b8",
            bg="#0f172a",
            font=("Segoe UI", 13)
        ).pack(pady=4)

        # STATUS
        self.status_label = tk.Label(
            top,
            text="Initializing...",
            fg="#38bdf8",
            bg="#0f172a",
            font=("Consolas", 11)
        )
        self.status_label.pack(pady=6)

        # =========================
        # PROGRESS BAR
        # =========================
        style = ttk.Style()
        style.configure(
            "boot.Horizontal.TProgressbar",
            troughcolor="#1e293b",
            background="#22c55e",
            thickness=8
        )

        self.progress = ttk.Progressbar(
            top,
            style="boot.Horizontal.TProgressbar",
            length=600,
            mode="determinate"
        )
        self.progress.pack(pady=8)

        # =========================
        # DETAIL LOG PANEL
        # =========================
        detail_frame = tk.Frame(self.window, bg="#020617")
        detail_frame.pack(fill="x", padx=20, pady=8)

        self.detail = tk.Text(
            detail_frame,
            height=6,  # optimized for space
            bg="#020617",
            fg="#22c55e",
            font=("Consolas", 10),
            borderwidth=0
        )
        self.detail.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(detail_frame, command=self.detail.yview)
        scroll.pack(side="right", fill="y")
        self.detail.configure(yscrollcommand=scroll.set)

        # =========================
        # DISCLAIMER (FULL WIDTH)
        # =========================
        self.disclaimer_frame = tk.Frame(self.window, bg="#020617")
        self.disclaimer_frame.pack_forget()

        self.disclaimer_text = tk.Text(
            self.disclaimer_frame,
            height=8,
            bg="#020617",
            fg="white",
            font=("Segoe UI", 11),
            wrap="word",
            borderwidth=0
        )
        self.disclaimer_text.pack(fill="x", padx=40, pady=(10, 5))

        self.disclaimer_text.insert(
            "end",
            "⚠ DEMONSTRATION SYSTEM — CLINICAL DISCLAIMER\n\n"
            "This system operates using synthetic and simulated clinical data.\n\n"
            "It is intended strictly for:\n"
            "• Educational purposes\n"
            "• System demonstration\n"
            "• Research and development\n\n"
            "It MUST NOT be used for:\n"
            "• Real patient care\n"
            "• Clinical decision-making\n"
            "• Diagnosis or treatment planning\n\n"
            "By proceeding, you acknowledge that you understand these limitations "
            "and agree to use this system responsibly."
        )

        self.disclaimer_text.config(state="disabled")

        self.agree_btn = tk.Button(
            self.disclaimer_frame,
            text="✔ AGREE & CONTINUE",
            bg="#22c55e",
            fg="black",
            font=("Segoe UI", 11, "bold"),
            padx=30,
            pady=10,
            relief="flat",
            command=self._agree
        )
        self.agree_btn.pack(pady=10)

        # =========================
        # FOOTER
        # =========================
        tk.Label(
            self.window,
            text="PeachBot v1.0  |  Clinical AI System",
            fg="#64748b",
            bg="#0f172a",
            font=("Segoe UI", 9)
        ).pack(side="bottom", pady=5)

        # =========================
        # BOOT STEPS
        # =========================
        self.steps = [
            ("Loading Patient Data...", self.load_patients),
            ("Loading Doctors...", self.load_doctors),
            ("Loading Clinical Knowledge...", self.load_knowledge),
            ("Finalizing...", self.final_step)
        ]

        self.step_index = 0
        self.callback = None

    # =========================
    def start(self, callback):
        self.callback = callback
        self.run_step()

    # =========================
    def run_step(self):
        if self.step_index < len(self.steps):
            msg, func = self.steps[self.step_index]

            self.status_label.config(text=msg)

            self.detail.insert("end", f"\n[✔] {msg}\n")
            self.detail.see("end")

            func()

            progress = int((self.step_index + 1) / len(self.steps) * 100)
            self.progress["value"] = progress

            self.step_index += 1
            self.window.after(700, self.run_step)

        else:
            self.status_label.config(text="Awaiting User Confirmation")
            self.disclaimer_frame.pack(fill="x", padx=20, pady=10)
            self.window.after(100, lambda: self.agree_btn.focus_set())

    # =========================
    # DATA LOADERS
    # =========================
    def load_patients(self):
        self.detail.insert("end", f"   → {len(self.patients)} patients loaded\n")
        for p in list(self.patients.values())[:3]:
            self.detail.insert(
                "end",
                f"   → {p.patient_id} | Age {p.age} | {p.gender}\n"
            )

    def load_doctors(self):
        self.detail.insert("end", f"   → {len(self.doctors)} doctors loaded\n")
        for d in list(self.doctors.values())[:3]:
            self.detail.insert(
                "end",
                f"   → {d.name} ({d.role})\n"
            )

    def load_knowledge(self):
        rules = self.rule_engine.rules
        self.detail.insert("end", f"   → {len(rules)} rules loaded\n")

        conditions = set()
        for r in rules[:5]:
            cond = r.get("entities", {}).get("condition")
            if cond:
                conditions.add(cond)

        self.detail.insert(
            "end",
            f"   → Conditions: {', '.join(conditions)}\n"
        )

    def final_step(self):
        self.detail.insert("end", "\nSystem integrity check: OK\n")

    # =========================
    def _agree(self):
        self.window.destroy()
        if self.callback:
            self.callback()